"""
core.py — E9 / E10 assembly, and the evaluator everything else differentiates.

E9  (Equation 10.2)
                 ⎡ Π_{i∈I} D_i^α_i(σ) · (s_US·D_prec)^α_prec(σ) ⎤^κ_sys
    DXY = Ψ_str · DXY₀ ⎢ ────────────────────────────────────── ⎥ · exp[(λ₁σ + λ₂σ²)Φ_sys] + ε
                 ⎣        Π_{j∈J} S_j^β_j(σ)                    ⎦

Four blocks, and the model's whole architecture is the claim that they are
multiplicatively separable in this particular way:

  Ψ_str, outside everything — the only factor that can take the dollar to a
    different REGIME rather than a different value.
  DXY₀, the normalisation — every D_i and S_j is 1 at t_base and Ψ_str(t_base) = 1,
    so the bracket equals one at the base period, term by term.
  The bracket raised to κ_sys — reflexivity scales the elasticity of the
    response to everything else; it does not add to the response.
  The safe-haven exponential — quadratic in stress, scaled by the reliability of
    the haven, additive in logs and therefore independent of the mechanical block.

Two index-set corrections are already applied and are easy to lose: I EXCLUDES
prec (ISSUES #7), and the separate precautionary factor keeps its state-dependent
exponent rather than a constant one (ISSUES #8).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .functions import blend, clamp, emergent, logistic, regime_weight, safe_log
from .layers import (
    Crisis, DEFAULT_OMEGA, KappaOut, PsychoOut, SigmaInputs, SigmaOut,
    f_hard_agg, k_psi_fn, kappa_sys, m_shock, phi_sys, psi_str,
    psycho_fixed_point, s_us_sys, sigma_sys,
)
from .registry import CHANNELS, DEMAND, D_PREC, LATENTS, SUPPLY, WEIGHTS
from .weightlayer import WeightSolution, solve_weights


# --------------------------------------------------------------------------- #
# Options — every departure from the book is here, and every one defaults off
# --------------------------------------------------------------------------- #

@dataclass
class Options:
    # Layer W
    enable_state_interaction: bool = True
    enable_weight_coupling: bool = True

    # E21 — regime-switched haven coefficients.  Remark 11.3: λ_1 "takes
    # opposite signs in the two regimes when estimated separately".  With Layer W
    # on, λ_1 and λ_2 carry loadings on σ and this is already active; the flag
    # below additionally splits them through Λ(σ) the way the elasticities are
    # split, which is the book's own device applied to its own problem.
    regime_switched_lambda: bool = False
    lam1_calm: float = -0.05
    lam1_crisis: float = 0.20

    # E22 — re-centred convexity, closing I37.  "A convex term in a bounded
    # variable delivers its largest increments in the middle of the range, and
    # every episode this book scores except the 2018 trade war begins with σ_sys
    # already high, so the mechanism is systematically smallest exactly where it
    # is asked to do the most work.  This is a property of the FUNCTIONAL FORM,
    # not an estimate, so no re-estimation of λ_2 removes it."  Re-centring on
    # the episode's entry state does remove it.
    recentre_convexity: bool = False
    sigma_anchor: Optional[float] = None    # None = use the run's entry σ

    # ISSUES #8 placement.  §6.7.2 puts the share INSIDE the base, because the
    # exponent form has the wrong limit: as s_US → 0 it tends to 1, so a panic
    # in which the dollar captures nothing would leave the numerator unchanged.
    # Equation (10.2) as printed still shows the exponent form.  The engine
    # takes §6.7.2 as canonical and keeps the printed form available, because
    # the two disagree and a reader holding the book should be able to see both.
    s_us_inside_base: bool = True

    # E26 — the Layer 5 → Layer 4 return path (I32).
    enable_return_path: bool = False

    # E27 — the reversal channel (I34): the sign graph has no arrow that lowers
    # S_off or T_frag, so the model has no representation of coercion that ends
    # coercion.
    enable_reversal: bool = False

    # E25 — the non-military exogenous leg in σ_sys (§5.5.3).
    enable_health_leg: bool = False

    # E28 — D_prec split across the curve (I40): "the two-year keeps the haven
    # property the thirty-year has lost."
    split_prec_curve: bool = False

    # The haven term responds to the funding leg rather than the composite.
    # §17.4: the funding leg regresses at t = +5.04, the composite worse than
    # its own friction component.  Off by default — this is a real departure.
    haven_on_funding_leg: bool = False

    # Layer 4 solution mode.
    #
    # "fixed_point" solves Equation (8.8), which is what Chapter 8 says the
    # psycho-technical state IS.  "exogenous" imposes H_soc and I_imp directly,
    # which is what Table 10.3 does for its baseline state and what every run in
    # §10.7 inherits.  The two are not the same thing and the book does not
    # reconcile them, so the engine offers both and `layers.implied_layer4`
    # reports the drivers the stated pair would require.
    psycho_mode: str = "fixed_point"       # or "exogenous"
    H_soc_exo: float = 0.30                # Table 10.3
    I_imp_exo: float = 0.30                # Table 10.3

    # Numerics
    sigma_c_bar: float = 1.30
    sigma_s_c: float = 0.55
    eta: float = 3.0
    # c_L0 and c_L1 are OPEN parameters introduced by ISSUES #13 to close the
    # H_soc <-> I_imp loop.  These values, with R_div = 0.3275, are the set under
    # which Table 10.3's stated baseline (H_soc = I_imp = 0.30) IS the fixed
    # point of Equation (8.8), rather than a pair imposed beside it.  Which of
    # the three absorbs the constraint is undetermined, because all three are
    # OPEN; the engine states its choice instead of hiding it.
    cL0: float = 0.80
    cL1: float = 1.18
    lam_f: float = 0.08
    t_now: float = 2026.75


# --------------------------------------------------------------------------- #
# World state
# --------------------------------------------------------------------------- #

def _unit_channels() -> Dict[str, float]:
    """Assumption 2.1 — every channel is an index number equal to 1 at t_base."""
    d = {c.key: 1.0 for c in DEMAND + SUPPLY}
    d[D_PREC.key] = 1.0
    return d


@dataclass
class WorldState:
    """Everything the engine needs that is not a weight."""
    channels: Dict[str, float] = field(default_factory=_unit_channels)
    latents: Dict[str, float] = field(default_factory=lambda: {k: v.default for k, v in LATENTS.items()})
    sigma_inputs: SigmaInputs = field(default_factory=SigmaInputs)
    DXY0: float = 100.0
    omega: Sequence[Crisis] = DEFAULT_OMEGA
    # ADDED, with E28: the two ends of the haven curve, when split_prec_curve is on.
    prec_short: float = 1.0
    prec_long: float = 1.0
    # ADDED, with E27: how hard the reversal arrow is being pulled.
    reversal: float = 0.0

    def copy(self) -> "WorldState":
        return WorldState(
            channels=dict(self.channels), latents=dict(self.latents),
            sigma_inputs=replace(self.sigma_inputs), DXY0=self.DXY0,
            omega=tuple(self.omega), prec_short=self.prec_short,
            prec_long=self.prec_long, reversal=self.reversal,
        )

    def shock(self, **kw) -> "WorldState":
        """Return a copy with channels / latents / sigma legs moved.

        Keys are matched against channels first, then latents, then the σ legs,
        then the two added scalars — so `state.shock(bank=0.88, R_US=0.45,
        p_vix=0.95)` reads the way an episode reads.
        """
        s = self.copy()
        for k, v in kw.items():
            if k in s.channels:
                s.channels[k] = v
            elif k in s.latents:
                s.latents[k] = v
            elif hasattr(s.sigma_inputs, k):
                setattr(s.sigma_inputs, k, v)
            elif hasattr(s, k):
                setattr(s, k, v)
            else:
                raise KeyError(f"unknown state key: {k}")
        return s


# --------------------------------------------------------------------------- #
# Result
# --------------------------------------------------------------------------- #

@dataclass
class Term:
    key: str
    symbol: str
    side: str
    level: float
    elasticity: float
    log_contrib: float        # κ_sys · α_i · ln D_i   (negative for supply)
    evidence: str


@dataclass
class Result:
    DXY: float
    ln_DXY: float

    # the four blocks of E9
    psi_str: float
    ln_bracket: float          # Σα ln D − Σβ ln S, before κ
    mechanical: float          # κ_sys · ln_bracket
    haven: float               # (λ₁σ + λ₂σ²)Φ_sys
    c0: float

    # layer states
    sigma: SigmaOut
    phi: float
    s_us: float
    kappa: KappaOut
    psycho: PsychoOut
    f_hard: float
    k_psi: float
    M_shock: float
    lam_weight: float          # Λ(σ) — the regime weight

    # Layer W
    weights: WeightSolution

    terms: List[Term]
    warnings: List[str] = field(default_factory=list)

    def block_table(self) -> List[Tuple[str, float]]:
        """The three blocks of Figure 10.2, in logs."""
        return [
            ("mechanical ×κ", self.mechanical),
            ("safe haven", self.haven),
            ("structural Ψ", math.log(max(self.psi_str, 1e-12))),
        ]


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #

def run(
    state: Optional[WorldState] = None,
    overrides: Optional[Dict[str, float]] = None,
    opt: Optional[Options] = None,
) -> Result:
    """Evaluate E9 once, with Layer W solved jointly with it.

    ORDER OF SOLUTION, and why it is this order.  Layer W depends on the state
    vector z, and z contains σ_sys, Φ_sys, H_soc, f_hard and Ψ_str, which are
    themselves computed from weights.  The engine therefore runs a short outer
    loop: evaluate the layers at the current weights, rebuild z, re-solve the
    weights, repeat.  It converges for the same reason the inner loop does —
    every map in the chain is a bounded logistic composition — and it is capped
    so that a configuration outside the contraction bound returns a labelled
    answer rather than spinning.
    """
    st = state or WorldState()
    opt = opt or Options()
    ov = dict(overrides or {})
    warn: List[str] = []

    L = st.latents
    z: Dict[str, float] = {
        "sigma": 0.35, "phi": 0.5, "sus": 0.70, "hsoc": 0.30,
        "iimp": 0.30, "fhard": 0.34, "rus": L.get("R_US", 0.2), "psi": 0.0,
    }

    wsol: Optional[WeightSolution] = None
    sig: Optional[SigmaOut] = None
    psy: Optional[PsychoOut] = None
    phi = s = f_h = kpsi = m_s = 0.0
    kap: Optional[KappaOut] = None
    psi = 1.0

    for _outer in range(12):
        wsol = solve_weights(
            z, overrides=ov,
            enable_state=opt.enable_state_interaction,
            enable_coupling=opt.enable_weight_coupling,
        )
        W = wsol.values

        # ---- Layer 1 ---------------------------------------------------- #
        sig = sigma_sys(
            st.sigma_inputs,
            w_sigma=W["w_sigma"], w_X=W["w_X"], w_F=W["w_F"],
            w_H=W["w_H"] if opt.enable_health_leg else 0.0,
            c_bar=opt.sigma_c_bar, s_c=opt.sigma_s_c,
        )

        # ---- Layer 4 (needs f_hard only if the return path is on) -------- #
        psy = psycho_fixed_point(
            A_alg=L["A_alg"], C_src=L["C_src"], P_AI=L["P_AI"], T_exp=L["T_exp"],
            R_div=L["R_div"], S_access=L["S_access"], R_fric=L["R_fric"],
            P_habit=L["P_habit"], E_sys=L["E_sys"],
            eta=opt.eta, cL0=opt.cL0, cL1=opt.cL1,
            b_F=W["b_F"] if opt.enable_return_path else 0.0,
            f_hard=z["fhard"],
        )
        if opt.psycho_mode == "exogenous":
            # Table 10.3's baseline imposes the pair rather than solving for it.
            # Keep the solved diagnostics — the contraction bound, the
            # amplification factor — attached to the imposed state so the user
            # can see the gap rather than lose it.
            H_e, I_e = clamp(opt.H_soc_exo), clamp(opt.I_imp_exo)
            V_e = (psy.V_meme / psy.H_soc * H_e) if psy.H_soc > 1e-12 else 0.0
            psy = replace(psy, H_soc=H_e, I_imp=I_e, V_meme=V_e,
                          B_phase=clamp(H_e * I_e))

        # ---- Layer 5 ----------------------------------------------------- #
        T_frag = L["T_frag"]
        S_off = L["S_off"]
        if opt.enable_reversal and st.reversal > 0:
            # E27, closing I34.  Coercion that ends coercion: the one arrow the
            # sign graph does not contain.  Both the fragmentation stock and the
            # immobilisation intensity decay toward their pre-episode level.
            r = W["r_rev"] * st.reversal
            T_frag = clamp(T_frag * (1.0 - r))
            S_off = clamp(S_off * (1.0 - r))

        f_h = f_hard_agg(L["C_alt"], T_frag, L["Au_sub"],
                         w_C=W["w_Calt"], w_T=W["w_Tfrag"],
                         w_CT=W["w_CT"], w_Au=W["w_gold"])
        kpsi = k_psi_fn(W["k_psi"], psy.H_soc, psy.V_meme, psy.I_imp)
        psi = psi_str(f_h, W["L_max"], W["theta_0"], kpsi)

        # ---- Layer 2 ----------------------------------------------------- #
        phi = phi_sys(L["G_pol"], L["R_US"], L["M_trust"], T_frag,
                      W["phi_0"], W["phi_G"], W["phi_R"], W["phi_M"], W["phi_T"])
        s = s_us_sys(L["G_pol"], L["R_US"], L["E_inf"], T_frag,
                     W["gam_0"], W["gam_G"], W["gam_R"], W["gam_E"], W["gam_T"])

        # ---- Layer 3 ----------------------------------------------------- #
        m_s = m_shock(opt.t_now, st.omega, lam_f=opt.lam_f)
        kap = kappa_sys(
            W["kappa_base"], L["V_USD"], m_s, L["A_meta"], sig.sigma, L["R_US"],
            psy.H_soc, psy.I_imp,
            W["a_V"], W["a_M"], W["a_A"], W["a_sigma"], W["kappa_R"],
            W["a_H"], W["a_I"],
        )

        z_new = {
            "sigma": sig.sigma,
            "phi": clamp(phi / 2.0),
            "sus": s,
            "hsoc": psy.H_soc,
            "iimp": psy.I_imp,
            "fhard": f_h,
            "rus": L["R_US"],
            "psi": clamp(1.0 - psi),
        }
        if max(abs(z_new[k] - z[k]) for k in z) < 1e-11:
            z = z_new
            break
        z = z_new
    else:
        warn.append("Vòng ngoài (layers ↔ Layer W) chưa hội tụ sau 12 lượt — "
                    "kiểm tra ràng buộc co rút.")

    assert wsol is not None and sig is not None and psy is not None and kap is not None
    W = wsol.values
    lam = regime_weight(sig.sigma, W["sigma_star"], W["theta"])

    # ---- Layer 0 ---------------------------------------------------------- #
    terms: List[Term] = []
    ln_bracket = 0.0

    for c in DEMAND:
        lvl = st.channels[c.key]
        a = blend(c.alpha_calm, c.alpha_crisis, lam)
        lc = a * safe_log(lvl)
        ln_bracket += lc
        terms.append(Term(c.key, c.symbol, "D", lvl, a, lc, c.evidence.value))

    # Precautionary demand, as its own factor (ISSUES #7 / #8).
    a_prec = W["alpha_prec"]
    if opt.split_prec_curve:
        # E28, closing I40.  One scalar for a whole curve is the defect; the
        # short end keeps the haven property the long end has lost, so the two
        # are weighted rather than averaged away.
        w2 = W["w_prec_short"]
        prec_level = math.exp(w2 * safe_log(st.prec_short) + (1 - w2) * safe_log(st.prec_long))
    else:
        prec_level = st.channels[D_PREC.key]

    if opt.s_us_inside_base:
        prec_base, prec_exp = s * prec_level, a_prec
    else:
        prec_base, prec_exp = prec_level, a_prec * s
    lc = prec_exp * safe_log(prec_base)
    # The base-period normalisation must hold term by term: at D_prec = 1 the
    # factor is s^α, not 1, so the constant part is absorbed into c₀ exactly as
    # DXY₀ absorbs every other base-period level (Equation 2.15).
    lc_base = prec_exp * safe_log(s if opt.s_us_inside_base else 1.0)
    ln_bracket += (lc - lc_base)
    terms.append(Term("prec", "D_prec", "D", prec_level, prec_exp, lc - lc_base,
                      D_PREC.evidence.value))

    for c in SUPPLY:
        lvl = st.channels[c.key]
        if c.key == "ext":
            # ISSUES #28 — log-safe attenuation.  A dampening quantity enters as
            # e^(−δx), never as (1 − x), so no single input switches a channel off.
            lvl = lvl * math.exp(-W["delta_off"] * L["S_off"])
        b = blend(c.alpha_calm, c.alpha_crisis, lam)
        lc = -b * safe_log(lvl)
        ln_bracket += lc
        terms.append(Term(c.key, c.symbol, "S", lvl, b, lc, c.evidence.value))

    mechanical = kap.kappa * ln_bracket

    # ---- the safe-haven exponential --------------------------------------- #
    sig_use = sig.sigma_fund if opt.haven_on_funding_leg else sig.sigma
    l1, l2 = W["lam_1"], W["lam_2"]
    if opt.regime_switched_lambda:
        l1 = blend(opt.lam1_calm, opt.lam1_crisis, lam)
    if opt.recentre_convexity:
        anchor = opt.sigma_anchor if opt.sigma_anchor is not None else 0.5
        d = sig_use - anchor
        haven = (l1 * d + l2 * d * d) * phi
    else:
        haven = (l1 * sig_use + l2 * sig_use * sig_use) * phi

    c0 = safe_log(st.DXY0)
    ln_dxy = safe_log(psi) + c0 + mechanical + haven

    # ---- the checks the book says must be made ---------------------------- #
    if phi <= 0:
        warn.append("Φ_sys ≤ 0: số hạng trú ẩn ĐỔI DẤU thay vì co lại "
                    "(§6.6.5). Assumption 2.5 loại vùng này bằng giả định, "
                    "không bằng cấu trúc.")
    if W["kappa_R"] >= 1.0:
        warn.append("κ_R ≥ 1: κ_sys âm, mô hình đảo ngược (Assumption 7.2).")
    if not psy.unique:
        warn.append(f"η·κ_A·g₁ = {psy.contraction:.2f} ≥ 4: điểm bất động Layer 4 "
                    f"không duy nhất — tối đa ba cân bằng, cái giữa bất ổn "
                    f"(Proposition 8.3). Kết quả đang đứng trên một nhánh.")
    if not wsol.unique:
        warn.append(f"‖C‖∞ = {wsol.coupling_norm:.2f} ≥ 4: hệ trọng số không có "
                    f"nghiệm duy nhất (E19).")
    if not wsol.converged:
        warn.append("Hệ trọng số chưa hội tụ trong số vòng lặp cho phép.")

    return Result(
        DXY=math.exp(ln_dxy), ln_DXY=ln_dxy,
        psi_str=psi, ln_bracket=ln_bracket, mechanical=mechanical,
        haven=haven, c0=c0,
        sigma=sig, phi=phi, s_us=s, kappa=kap, psycho=psy,
        f_hard=f_h, k_psi=kpsi, M_shock=m_s, lam_weight=lam,
        weights=wsol, terms=terms, warnings=warn,
    )


def make_evaluator(
    state: Optional[WorldState] = None,
    opt: Optional[Options] = None,
    base_overrides: Optional[Dict[str, float]] = None,
) -> Callable[[Dict[str, float]], float]:
    """A closure returning ln DXY for a weight vector — what E20 differentiates."""
    st = state or WorldState()
    o = opt or Options()
    base = dict(base_overrides or {})

    def f(ov: Dict[str, float]) -> float:
        merged = dict(base)
        merged.update(ov)
        return run(st, merged, o).ln_DXY

    return f


# --------------------------------------------------------------------------- #
# E10 — comparative statics
# --------------------------------------------------------------------------- #

def elasticities(res: Result) -> Dict[str, float]:
    """Equation (10.6) — the workhorses of Part II.

        ∂ln DXY/∂ln D_i = κ_sys·α_i(σ)
        ∂ln DXY/∂ln S_j = −κ_sys·β_j(σ)
        ∂ln DXY/∂ln Ψ_str = 1

    The central multiplicative claim is in the κ_sys: a one per cent rise in
    transactional demand moves the dollar by κ_sys·α_trans per cent, so the same
    shock has a different price impact in a reflexive market than in a quiet
    one, WITHOUT any elasticity having changed.
    """
    out = {t.symbol: (1 if t.side == "D" else -1) * res.kappa.kappa * t.elasticity
           for t in res.terms}
    out["Ψ_str"] = 1.0
    return out


def d_ln_dxy_d_sigma(res: Result, opt: Optional[Options] = None) -> Dict[str, float]:
    """Equation (10.7) — the response to stress has THREE components, not one,
    and the empirical work of Chapter 5 estimated a reduced form containing all
    three at once and cannot separate them.

        direct haven : (λ₁ + 2λ₂σ)·Φ_sys
        reflexive    : (∂κ/∂σ)·ln(D*/S*) = a_σκ/(1+a_σσ) · ln_bracket
        regime       : κ·Σ(∂α_i/∂σ)·ln D_i − …

    Proposition 10.3: a sign change requires λ₁ < 0.  Convexity alone cannot
    produce one; it can only make an already-positive response steeper.  And
    Φ_sys > 0 multiplies the whole expression, so a regime in which the dollar
    is not a reliable haven FLATTENS the response toward zero rather than
    inverting it — the model has no mechanism for a genuinely risk-on dollar.
    """
    W = res.weights.values
    sg = res.sigma.sigma
    direct = (W["lam_1"] + 2.0 * W["lam_2"] * sg) * res.phi

    a_s = W["a_sigma"]
    reflexive = (a_s / (1.0 + a_s * sg)) * res.kappa.kappa * res.ln_bracket

    th, ss = W["theta"], W["sigma_star"]
    dlam = th * res.lam_weight * (1.0 - res.lam_weight)
    regime = 0.0
    for t in res.terms:
        ch = CHANNELS.get(t.key)
        if ch is None or t.key == "prec":
            continue
        gap = ch.alpha_crisis - ch.alpha_calm
        regime += (1 if t.side == "D" else -1) * gap * dlam * safe_log(t.level)
    regime *= res.kappa.kappa

    return {"direct_haven": direct, "reflexive": reflexive,
            "regime": regime, "total": direct + reflexive + regime}


def smile_threshold(res: Result) -> Optional[float]:
    """σ† = −λ₁/(2λ₂) ∈ (0,1), where the haven term changes sign.  Returns None
    when the parameter set cannot produce a smile — which, on the book's own
    stated set (λ₁ = +0.08), it cannot, and that is Proposition 10.3 rather than
    a bug."""
    W = res.weights.values
    l1, l2 = W["lam_1"], W["lam_2"]
    if l2 <= 0 or l1 >= 0:
        return None
    t = -l1 / (2.0 * l2)
    return t if 0.0 < t < 1.0 else None
