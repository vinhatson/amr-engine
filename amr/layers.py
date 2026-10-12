"""
layers.py — Layers 1 to 5 of the canonical model: E3, E4, E5, E6, E7/E7b, E8,
plus the crisis-memory formulas E11–E14 that §7.4 relocates into Layer 3.

Each function is the book's canonical (post-ISSUES) form, not the original
paper's.  Where this engine departs, the departure is behind a flag that is off
by default and is named in the docstring.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .functions import blend, clamp, dlogistic, logistic, regime_weight


# =========================================================================== #
# Layer 1 — E3, the systemic instability index
# =========================================================================== #

@dataclass
class SigmaInputs:
    """All four legs enter as percentile ranks in [0, 1] (Assumption 5.1)."""
    p_vix: float = 0.42          # market-priced volatility
    p_bondvol: float = 0.42      # 21-day realised-vol substitute for the paywalled MOVE
    p_gpr: float = 0.30          # Caldara-Iacoviello geopolitical risk — war and terrorism
    p_stlfsi: float = 0.33       # the friction leg
    p_health: float = 0.00       # ADDED: the non-military exogenous leg (§5.5.3)


@dataclass
class SigmaOut:
    sigma: float                 # the bounded index
    composite: float             # C_t before standardisation
    market_share: float          # fraction of C_t carried by the market legs
    news_share: float            # fraction carried by the news count
    health_share: float
    friction_mult: float
    sigma_fund: float            # ADDED: the funding leg alone
    sigma_gen: float             # ADDED: the general-stress legs alone


def sigma_sys(
    s: SigmaInputs,
    w_sigma: float,
    w_X: float,
    w_F: float,
    w_H: float = 0.0,
    c_bar: float = 1.30,
    s_c: float = 0.55,
) -> SigmaOut:
    """E3 canonical — Equation (5.2).

        C_t = (w_σ·½(p_VIX + p_bondvol) + w_X·p_GPRD + w_H·p_health)·(1 + w_F·p_STLFSI)
        σ_sys = Λ((C_t − C̄) / s_C)

    (C̄, s_C) are the sample mean and standard deviation of C_t.  The book is
    explicit that this makes σ_sys sample-dependent and therefore NOT a real-time
    series: "recomputing it on a shorter sample changes every value."  The
    defaults here reproduce the book's reported range on its own 2006–2026
    sample; pass your own when you have one.

    §5.5.4 is the warning this function must carry: after the rank transform,
    the weights are the only thing left that determines relative influence.
    There is no variance to scale and no data-driven force that shrinks a
    component carrying little information.  At w_σ = w_X = 1, half the
    pre-friction composite is a count of newspaper articles.

    The w_H leg is ADDED (E25).  §5.5.3: the X_pand proxy measures war and
    terrorism, so 2020 — the clearest non-financial shock in the sample — gains
    nothing from it.  Default 0 reproduces the book exactly.
    """
    market = 0.5 * (s.p_vix + s.p_bondvol)
    base = w_sigma * market + w_X * s.p_gpr + w_H * s.p_health
    friction = 1.0 + w_F * s.p_stlfsi
    composite = base * friction

    total = max(base, 1e-12)
    z = (composite - c_bar) / max(s_c, 1e-9)

    # The two legs the book's own evidence says behave differently: the funding
    # leg regresses on the dollar at t = +5.04, the geopolitical leg at -0.19.
    z_fund = (s.p_stlfsi - 0.5) * 4.0
    z_gen = (market - 0.5) * 4.0

    return SigmaOut(
        sigma=clamp(logistic(z)),
        composite=composite,
        market_share=w_sigma * market / total,
        news_share=w_X * s.p_gpr / total,
        health_share=w_H * s.p_health / total,
        friction_mult=friction,
        sigma_fund=clamp(logistic(z_fund)),
        sigma_gen=clamp(logistic(z_gen)),
    )


# =========================================================================== #
# Layer 2 — E4 shelter credibility, E5 the safe-flow share
# =========================================================================== #

def phi_sys(
    G_pol: float, R_US: float, M_trust: float, T_frag: float,
    phi_0: float, phi_G: float, phi_R: float, phi_M: float, phi_T: float,
) -> float:
    """E4 canonical — Equation (6.5), with the ISSUES #1 sign correction:

        Φ_sys = φ_0 + φ_G·G_pol − φ_R·R_US + φ_M·M_trust − φ_T·T_frag

    Affine, not multiplicative: the pillars substitute.  The rejected
    multiplicative form would zero out shelter credibility on a total loss of
    judicial independence even with the deepest bond market in the world still
    functioning (§6.6.3).

    Failure mode the book names and this function does not hide: E4 can go
    negative for extreme inputs, which would FLIP the sign of the whole
    safe-haven term rather than merely shrinking it.  Assumption 2.5 excludes
    that region by assumption, not by construction — so `feasibility.py` checks
    it rather than this function silently clipping.
    """
    return phi_0 + phi_G * G_pol - phi_R * R_US + phi_M * M_trust - phi_T * T_frag


def s_us_sys(
    G_pol: float, R_US: float, E_inf: float, T_frag: float,
    gam_0: float, gam_G: float, gam_R: float, gam_E: float, gam_T: float,
) -> float:
    """E5 — Equation (6.6), unchanged from the original.

        s_US,sys = Λ(γ_0 + γ_G·G_pol − γ_R·R_US − γ_E·E_inf − γ_T·T_frag)

    A share, so it must saturate: the dollar cannot capture more than all of a
    panic, and the marginal effect of more geopolitical power must vanish as the
    share approaches one.  That saturation is a result, not a nuisance: E15b's
    s(1−s) is 0.25 at s = 0.50 and 0.09 at s = 0.90, so military capability buys
    less for a dominant currency than for a contested one (§15.3.3).
    """
    return logistic(gam_0 + gam_G * G_pol - gam_R * R_US - gam_E * E_inf - gam_T * T_frag)


def d_s_us_d_gpol(s: float, gam_G: float) -> float:
    """E15b — ∂s_US/∂G_pol = s(1−s)·γ_G.  First-order only: the logistic's
    curvature over-states a large shock near s = 0.5 and under-states it in the
    tails (ISSUES #22)."""
    return s * (1.0 - s) * gam_G


# =========================================================================== #
# Layer 3 — E6 reflexive acceleration, E11–E14 crisis memory
# =========================================================================== #

@dataclass(frozen=True)
class Crisis:
    year: float
    severity: float   # the original states 2008 = 10/10, 2001 = 6/10


# 2020 is deliberately absent: the original assigns it no severity, and
# inventing one would put a number in the engine that no source supports.
# 2029 is dropped as a hypothetical future crisis inside a formula example
# (ISSUES #20).
DEFAULT_OMEGA: Tuple[Crisis, ...] = (Crisis(2008.75, 10.0), Crisis(2001.7, 6.0))


def m_shock(
    t: float,
    omega: Sequence[Crisis] = DEFAULT_OMEGA,
    lam_f: float = 0.08,
    T_career: float = 25.0,
    normalise: float = 13.0,
) -> float:
    """E11–E13 — crisis memory, faded by two decays of different character.

        M_shock(t) = Σ_k S_k · e^(−λ_f (t − t_k)) · ρ_gen(t, t_k)
        ρ_gen = max(0, 1 − (t − t_k)/T_career)

    Psychological decay is continuous and never complete; generational decay is
    linear and TERMINATES.  A model with only the first predicts institutional
    memory fading smoothly; with both, it predicts a hard horizon.

    T_career = 25 is implied by the original's own worked example (ρ ≈ 0.6 ten
    years after 2008), not chosen independently (§7.4.2).

    λ_f rises with V_meme.  That is the countervailing channel of §7.6.2: the
    psycho-technical layer reaches κ_sys by two routes with opposite signs, and
    which dominates is recorded by the book as an open sign.  `weights.a_M`
    carries a negative loading on H_soc so that the engine computes it instead
    of asserting it.

    `normalise` rescales the raw sum into [0, 1] as every latent modulator must
    be (Assumption 2.2); 13.0 is the book's own 2008 figure under slow forgetting.
    """
    total = 0.0
    for c in omega:
        age = t - c.year
        if age < 0:
            continue
        rho = max(0.0, 1.0 - age / T_career)
        total += c.severity * math.exp(-lam_f * age) * rho
    return clamp(total / max(normalise, 1e-9))


def m_shock_eff(m: float, alpha_res: float, A_alg: float, sim: float) -> float:
    """E14 — synthetic re-activation: a faded memory revived without a new crisis.

        M_shock^eff = M_shock·(1 + α_res·A_alg·Sim(t, t_k))
    """
    return clamp(m * (1.0 + alpha_res * A_alg * sim))


@dataclass
class KappaOut:
    kappa: float
    factors: Dict[str, float]
    kappa_max: float


def kappa_sys(
    kappa_base: float,
    V_USD: float, M_shock_: float, A_meta: float, sigma: float, R_US: float,
    H_soc: float, I_imp: float,
    a_V: float, a_M: float, a_A: float, a_sigma: float, kappa_R: float,
    a_H: float, a_I: float,
) -> KappaOut:
    """E6 canonical — Equation (7.5), after ISSUES #3 and #3a:

        κ_sys = κ_base(1+a_V V)(1+a_M M)(1+a_A A)(1+a_σ σ)(1−κ_R R_US)(1+a_H H)(1+a_I I)

    Every one of the seven drivers enters the same way.  A driver at zero leaves
    κ_sys unchanged; drivers compound rather than substitute.  The (1+ax) form
    is the minimal shape with that property that also leaves κ_sys at κ_base
    when every driver is off.

    Before ISSUES #3a, H_soc and I_imp entered BARE, with three consequences
    none of which the original claims: the log-elasticity was 1/H_soc, which
    diverges as homogeneity approaches zero; κ_sys → 0 as H_soc → 0, so a
    perfectly heterogeneous market would transmit nothing at all; and those two
    were the only drivers whose absence was destructive rather than neutral.

    κ_sys is an EXPONENT on the demand-supply bracket, not a coefficient in it.
    That is the model's sharpest structural claim: reflexivity does not add to
    the dollar's response, it scales the elasticity of the response to
    everything else.  A doubling of κ_sys does not double the move; it squares
    the ratio's effect on it.

    Identification, stated rather than buried: seven coefficients multiply five
    unobservable inputs and two more that are the output of a fixed-point
    calculation.  Chapter 11 can hope to identify κ_sys as a single state, never
    its decomposition (Proposition 11.1).
    """
    f = {
        "κ_base": kappa_base,
        "(1+a_V·V_USD)": 1.0 + a_V * V_USD,
        "(1+a_M·M_shock)": 1.0 + a_M * M_shock_,
        "(1+a_A·A_meta)": 1.0 + a_A * A_meta,
        "(1+a_σ·σ_sys)": 1.0 + a_sigma * sigma,
        "(1−κ_R·R_US)": 1.0 - kappa_R * R_US,
        "(1+a_H·H_soc)": 1.0 + a_H * H_soc,
        "(1+a_I·I_imp)": 1.0 + a_I * I_imp,
    }
    k = 1.0
    for v in f.values():
        k *= v
    kmax = (kappa_base * (1 + a_V) * (1 + a_M) * (1 + a_A)
            * (1 + a_sigma) * (1 + a_H) * (1 + a_I))
    return KappaOut(kappa=k, factors=f, kappa_max=kmax)


# =========================================================================== #
# Layer 4 — E7 / E7b as one map, and its fixed point
# =========================================================================== #

@dataclass
class PsychoOut:
    H_soc: float
    I_imp: float
    kappa_A: float
    g0: float
    g1: float
    contraction: float      # η·κ_A·g_1 — unique and globally attracting below 4
    unique: bool
    amplification: float    # 1/(1 − T'), the number behind "hyper-brittleness"
    iterations: int
    V_meme: float
    B_phase: float


def psycho_fixed_point(
    A_alg: float, C_src: float, P_AI: float, T_exp: float, R_div: float,
    S_access: float, R_fric: float, P_habit: float, E_sys: float,
    eta: float = 3.0,
    cL0: float = 0.25, cL1: float = 0.55,
    v0: float = 0.4, bA: float = 0.8, bP: float = 0.6,
    b_F: float = 0.0, f_hard: float = 0.0,
    tol: float = 1e-12, max_iter: int = 500,
) -> PsychoOut:
    """E7 ∘ E7b — Equation (8.8).  Two formulas become one map from [0,1] to itself:

        T(H) = F(G(H)),  G(H) = g_0 + g_1 H,  F(I) = Λ(η(κ_A I − R_div))
        κ_A = A_alg·C_src·P_AI·T_exp
        g_0 = K·c_L0, g_1 = K·c_L1, K = S_access·P_habit·E_sys/(1 + R_fric)

    and the psycho-technical state is the fixed point H* = T(H*).

    Proposition 8.1 (existence, UNCONDITIONAL): G is affine into [0,1],
    F is continuous into (0,1) strictly, so T(H) − H changes sign on [0,1].
    The layer always has an equilibrium.  The question is never whether the loop
    settles; it is where, and whether that somewhere is unique.

    Proposition 8.2: sup|T'(H)| = ¼·η·κ_A·g_1, SHARP and attained.  Below 4 the
    map is a contraction — unique fixed point, globally attracting, geometric
    convergence.  Since κ_A ≤ 1 and g_1 ≤ 1, η < 4 alone suffices.

    Proposition 8.3: above the bound there are at most three equilibria, the
    middle one unstable — which LOCATES the tipping threshold the original
    describes throughout and never locates.  Remark 10.1: the irreversibility
    the original attributes to Layer 5 is in fact here.

    Equation (8.6), closing ISSUES #13: C_loop = c_L0 + c_L1·H_soc.  The
    original says H_soc and I_imp "mutually reinforce" and its equations are
    one-way; the loop is closed at the one driver where the mechanism is
    unambiguous.  Homogeneity shortens the cognitive loop, the loop raises
    impulse efficiency, impulse efficiency raises homogeneity.

    b_F is ADDED and zero by default (E26, closing I32).  It appends
    (1 + b_F·f_hard) to V_meme, giving Layer 5 the inbound edge to Layer 4 that
    Remark 10.2 records as absent — the trigger event spawning the transmissible
    narrative, stage 2 → stage 3.  The book writes this exact term and declines
    it on estimability grounds; here the omission is recoverable, not silent.
    """
    kappa_A = A_alg * C_src * P_AI * T_exp
    K = S_access * P_habit * E_sys / (1.0 + R_fric)
    g0, g1 = K * cL0, K * cL1

    # Assumption 8.3 admissibility: g0 >= 0 and g0 + g1 <= 1 so I_imp stays in [0,1].
    if g0 + g1 > 1.0:
        scale = 1.0 / (g0 + g1)
        g0, g1 = g0 * scale, g1 * scale

    H = 0.5
    it = 0
    for it in range(1, max_iter + 1):
        I = g0 + g1 * H
        H_new = logistic(eta * (kappa_A * I - R_div))
        if abs(H_new - H) < tol:
            H = H_new
            break
        H = H_new

    I = g0 + g1 * H
    contraction = 0.25 * eta * kappa_A * g1

    # The derivative at the fixed point, and the amplification factor it gives.
    Tp = eta * kappa_A * dlogistic(eta * (kappa_A * I - R_div)) * g1
    amp = 1.0 / (1.0 - Tp) if Tp < 1.0 else float("inf")

    # E8.2 — V_meme.  A_alg and P_AI enter as (1 + b x) on the ISSUES #3a
    # reasoning; H_soc enters BARE, because a narrative cannot propagate through
    # a population that shares no frame with which to receive it.
    V = v0 * H * (1.0 + bA * A_alg) * (1.0 + bP * P_AI) * (1.0 + b_F * f_hard)

    # B_phase — a consequence variable with an equation and no place in E9.
    B = clamp(H * I)

    return PsychoOut(H_soc=clamp(H), I_imp=clamp(I), kappa_A=kappa_A, g0=g0, g1=g1,
                     contraction=contraction, unique=contraction < 4.0,
                     amplification=amp, iterations=it, V_meme=V, B_phase=B)


# =========================================================================== #
# Layer 5 — E8, the cliff function
# =========================================================================== #

def f_hard_agg(
    C_alt: float, T_frag: float, Au_sub: float,
    w_C: float, w_T: float, w_CT: float, w_Au: float,
) -> float:
    """E24 — ADDED.  The aggregator Assumption 9.1 assumes and never writes.

        C_alt^wide = (1 − w_Au)·C_alt + w_Au·Au_sub
        f_hard = clamp(w_C·C_alt^wide + w_T·T_frag − w_CT·C_alt^wide·T_frag)

    Two decisions are visible here rather than hidden.

    First, C_alt is WIDENED.  §17.6.3 is the one place in the book where a
    rescue hypothesis survived its own test: reserve-asset substitution into
    gold belongs in C_alt and is currently outside it.  A C_alt that counts only
    payment rails will keep measuring the wrong exit.  w_Au is the share of the
    wide measure carried by reserve substitution.

    Second, the cross term is SUB-additive by default (w_CT > 0): fragmentation
    without an exit route accumulates pressure the dollar still absorbs, and an
    exit route nobody is fragmenting away from is capacity nobody uses.  The
    hard drivers bite together, not separately.  Set w_CT < 0 for the
    super-additive reading and the engine will carry it.

    Without f_hard, Chapter 9 cannot be tested at all — §17.8 item three.
    """
    C_wide = (1.0 - w_Au) * C_alt + w_Au * Au_sub
    return clamp(w_C * C_wide + w_T * T_frag - w_CT * C_wide * T_frag)


def psi_str(f_hard: float, L_max: float, theta_0: float, k_psi: float) -> float:
    """E8 — Equation (9.2).

        Ψ_str = 1 − L_max·Λ(k_Ψ(f_hard − θ_0)),   Ψ_min = 1 − L_max

    Three phases, and the book is careful about the third.  Plateau: for
    f_hard ≪ θ_0 erosive forces accumulate with almost no visible effect — and
    the model gets that from the functional form rather than from a mechanism,
    since D_net appears nowhere in E8.  Tipping point: at f_hard = θ_0 the
    logistic passes ½, Ψ_str is exactly 1 − L_max/2, and the rate of decline is
    maximal at L_max·k_Ψ/4.  "Freefall": the original's word, and it overstates
    the mathematics — the fastest decline is AT the threshold, not after it.
    What follows is a rapid but DECELERATING approach to the floor.

    Erosion is always downward: Ψ_str ↓, never ↑ (ISSUES #2).

    Empirical standing, carried at the point of the claim: the cliff is not
    supported and cannot be refuted either.  The reserve share did fall, 72.1 to
    57.1 per cent, t = −16.9 — but E8 requires the decline to ACCELERATE below
    the threshold and it decelerates, quadratic term +0.0115, t = +3.84
    (Proposition 9.2).  Because f_hard has no measure, that cannot be turned
    into a rejection (Proposition 9.3).  §17.6.3 then shows the erosion was
    measured on the wrong reserve aggregate: on FX + gold the decline accelerates.
    """
    return 1.0 - L_max * logistic(k_psi * (f_hard - theta_0))


# Baseline anchors for the k_Psi normalisation: Table 10.3's stated baseline
# state, H_soc = I_imp = 0.30, and the V_meme that follows from it at the
# default E8.2 parameters.
_KPSI_H0, _KPSI_I0 = 0.30, 0.30
_KPSI_C = (2.2, 1.0, 0.8)   # loadings on H_soc, V_meme, I_imp
_KPSI_V0 = 0.23617          # V_meme at the baseline state, from E8.2 at the defaults


def k_psi_fn(k_base: float, H_soc: float, V_meme: float, I_imp: float,
             V0: float = _KPSI_V0) -> float:
    """k_Ψ(H_soc, V_meme, I_imp) — the book names the arguments and not the form.

    Written as a NORMALISED multiplier so that k_base reads as the value itself
    at the Table 10.3 baseline rather than as the base of an unanchored product:

        k_Ψ = k_base · Π(1 + c_x·x) / Π(1 + c_x·x₀)

    At H_soc = I_imp = 0.30 this returns k_base exactly, which is the book's
    stated k_Ψ = 6.  Under the narrative shock of §10.7.4, where H_soc and I_imp
    saturate, the loadings above carry it to roughly 27 — against the 28 the
    book reports.  The coefficients are chosen to reproduce that one documented
    transition and nothing else; they are an ENGINE_CONVENTION, since the book
    gives the arguments of k_Ψ and never its form.

    Assumption 9.2 keeps speed and position separate: the narrative layer enters
    only through k_Ψ, the hard drivers only through f_hard and θ_0.  Narrative
    changes how fast the transition happens, not where the threshold is.

    §9.8 calls that "the most consequential place where this chapter follows the
    original rather than departing from it", since one could hold that belief
    itself lowers the threshold — a currency is used because it is expected to be
    used.  The engine keeps Assumption 9.2 by default and exposes the departure
    as a loading of θ_0 on H_soc, which is zero unless you set it.
    """
    cH, cV, cI = _KPSI_C
    num = (1.0 + cH * H_soc) * (1.0 + cV * V_meme) * (1.0 + cI * I_imp)
    den = (1.0 + cH * _KPSI_H0) * (1.0 + cV * V0) * (1.0 + cI * _KPSI_I0)
    return k_base * num / max(den, 1e-12)


@dataclass
class ImpliedLayer4:
    """What the Layer-4 drivers must satisfy for a STATED (H, I) to be a fixed point."""
    H_target: float
    I_target: float
    K_required: float
    R_div_required: float
    kappa_A_assumed: float
    consistent: bool
    note_vi: str


def implied_layer4(H: float, I: float, kappa_A: float, eta: float = 3.0,
                   cL0: float = 0.25, cL1: float = 0.55) -> ImpliedLayer4:
    """Back-solve Equation (8.8) for the drivers a stated psycho-technical state
    implies.

    Why this function exists.  Table 10.3 states a baseline H_soc = I_imp = 0.30,
    and Chapter 8 makes the pair the FIXED POINT of a map, not a free input.  The
    two are only compatible for particular values of K and R_div, and the book
    states neither.  Rather than quietly imposing the stated pair or quietly
    solving the map, the engine does both and reports what the stated pair would
    require:

        I = K(c_L0 + c_L1·H)        ⟹  K = I / (c_L0 + c_L1·H)
        H = Λ(η(κ_A·I − R_div))     ⟹  R_div = κ_A·I − logit(H)/η

    An R_div outside [0, 1] or a K implying g_0 + g_1 > 1 means the stated
    baseline is NOT reachable as an equilibrium of the layer at that κ_A, which
    is a finding about the parameter set rather than an error in it.
    """
    denom = cL0 + cL1 * H
    K = I / denom if denom > 0 else float("inf")
    R = kappa_A * I - logit_safe(H) / max(eta, 1e-9)
    g0, g1 = K * cL0, K * cL1
    ok = (0.0 <= R <= 1.0) and (g0 >= 0.0) and (g0 + g1 <= 1.0 + 1e-9)
    if ok:
        note = (f"Trạng thái nền (H={H:.2f}, I={I:.2f}) ĐẠT được như một điểm bất động "
                f"nếu R_div = {R:.3f} và K = {K:.3f}.")
    else:
        why = []
        if not (0.0 <= R <= 1.0):
            why.append(f"R_div = {R:.3f} nằm ngoài [0,1]")
        if g0 + g1 > 1.0 + 1e-9:
            why.append(f"g₀+g₁ = {g0+g1:.3f} > 1, vi phạm Assumption 8.3")
        note = (f"Trạng thái nền (H={H:.2f}, I={I:.2f}) KHÔNG phải điểm bất động của "
                f"Equation (8.8) với κ_A = {kappa_A:.4f}: " + "; ".join(why) +
                ". Table 10.3 áp đặt cặp này chứ không giải nó.")
    return ImpliedLayer4(H, I, K, R, kappa_A, ok, note)


def logit_safe(u: float) -> float:
    u = min(max(u, 1e-12), 1.0 - 1e-12)
    return math.log(u / (1.0 - u))
