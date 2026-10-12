"""
weightlayer.py — Layer W, the parametric layer.  E17 to E22.

WHAT THIS ADDS, AND WHY IT IS NOT A DIFFERENT MODEL
---------------------------------------------------
In the monograph every weight is a constant.  Chapter 17 reports that the data
decline to hold two of them constant — "λ_1 is a constant in E9 and takes
opposite signs in the two regimes when estimated separately" (Remark 11.3) — and
§17.8's second research item says the mechanical coefficients DO scale with
σ_sys (Table 11.8), so recovering κ_sys as a single latent state is the most
promising single step available.

Layer W is that step, generalised.  It makes every weight a bounded function of
the model's own state, and it lets weights respond to each other.  Three design
constraints keep it inside the book rather than beside it:

  1. EXACT NESTING.  With all loadings at zero, every weight returns its base
     value and the engine reproduces E9 term for term.  The extension is
     therefore testable against the thing it extends: `tests/test_nesting.py`
     asserts it to machine precision.

  2. NO NEW FUNCTIONAL FORM.  Layer W is built from the same logistic that
     carries σ_sys, s_US,sys, H_soc, Ψ_str and Λ(σ).  §10.4: "The book has one
     S-shape."  It still does.

  3. NO WEIGHT LEAVES ITS ZONE.  Because the logistic maps onto (0,1) strictly,
     E17 maps onto (lo, hi) strictly.  Every bound ISSUES #9, #14, #26 and #3a
     imposed survives any interaction term whatsoever.  κ_R cannot reach 1.
     Ψ_str cannot leave [Ψ_min, 1].  The cumulative payoff of those four items
     is not spent to buy state dependence.

Layer W is numbered 6 but it is TRANSVERSE, not stacked.  Layers 0–5 are a
modulation cascade in which each stratum changes how violently the one below it
transmits.  Layer W does not sit above Layer 5; it cuts across all six, because
a weight belongs to whichever layer its equation belongs to.  Calling it a
seventh storey would misdescribe the architecture (Table 10.4's four
mathematical roles are unchanged by it).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from .functions import logistic, logit
from .registry import WEIGHTS, Weight, Z_DRIVERS


# --------------------------------------------------------------------------- #
# The baseline state vector z⁰
# --------------------------------------------------------------------------- #
#
# Table 10.3's "Baseline state" row, plus the Φ_sys, s_US,sys and Ψ_str that the
# rest of that table produces there.
#
# Every state loading in E17 acts on the DEPARTURE (z_m − z⁰_m), never on the
# level.  That is what keeps the base values meaning what Table 10.3 means by
# them: at the baseline state every weight equals its stated base however large
# its loadings are, and a loading then reads as "the effect of moving this
# driver one full unit away from baseline" — which is the interpretation the
# book's own Notation convention 3 gives to a coefficient on a bounded variable.
#
# Without the centring, Layer W would silently re-calibrate the book's own
# stated parameter set the moment it was switched on, and no run could be
# compared with Figure 10.2.

Z_BASELINE: Dict[str, float] = {
    "sigma": 0.35,    # Table 10.3, baseline state
    "phi":   0.35,    # Φ_sys = 0.70, normalised by Φ_max = 2
    "sus":   0.70,    # Table 10.3, precautionary block
    "hsoc":  0.30,    # Table 10.3, baseline state
    "iimp":  0.30,    # Table 10.3, baseline state
    "fhard": 0.34,    # Table 10.3: "f_hard = 0.34 at t_0"
    "rus":   0.20,    # Table 10.3, baseline state
    "psi":   0.0969,  # 1 − Ψ_str at that f_hard, with θ_0 = 0.50, k_Ψ = 6, L_max = 0.35
}


# --------------------------------------------------------------------------- #
# E18 — the weight-pair coupling matrix
# --------------------------------------------------------------------------- #
#
# An entry C[(k, j)] says: when weight j sits above its base position inside its
# own zone, weight k is pulled up (positive) or down (negative) with it.
#
# Every entry below names a mechanism the monograph argues for.  There are no
# entries added for symmetry, for completeness, or because a pair looked
# plausible.  A coupling with no mechanism is a free parameter with no evidence,
# which is the thing Chapter 11 spends forty pages counting.

DEFAULT_COUPLING: Dict[Tuple[str, str], float] = {

    # Hyper-brittleness (§7.8).  Stress sensitivity and belief homogeneity are
    # the two halves of one claim: shocks transmit violently because agents
    # react the same way.  "Waves become walls."
    ("a_sigma", "a_H"): 0.45,
    ("a_H", "a_sigma"): 0.30,

    # Dual amplification (§7.6).  Homogeneity and impulse efficiency have the
    # same technological cause — the same platforms supply all the drivers of
    # both — so they are correlated in practice, which §8.3 notes while
    # Assumption 8.1 treats the drivers as independent.
    ("a_H", "a_I"): 0.40,
    ("a_I", "a_H"): 0.40,

    # The countervailing channel (§7.6.2), which the original does not note.
    # The psycho-technical layer reaches κ_sys twice with opposite signs:
    # directly through H_soc and I_imp, which raise it, and indirectly through
    # V_meme → λ_f → M_shock, which lowers it.  Tripling λ_f from 0.05 to 0.15
    # cuts memory in 2018 from 4.9 to 1.8.  The book records this as an OPEN
    # SIGN rather than resolving it by assertion; this entry makes it computable
    # and the net effect on κ_sys readable off the run.
    ("a_M", "a_H"): -0.55,

    # §7.7.4.  Without (1 + a_σ σ_sys) the model has no representation of
    # κ'(σ) > 0, "on which the entire convexity claim rests".  The quadratic
    # haven coefficient is the other place that claim is carried.  They are one
    # convexity claim written in two equations, so they move together.
    ("lam_2", "a_sigma"): 0.35,

    # The double-counting guard, made explicit.  R_US sets the LEVEL of haven
    # demand in Layer 2 (through φ_R) and degrades its TRANSMISSION in Layer 3
    # (through κ_R): "a dollar issued by a politically unstable United States
    # remains a haven but becomes a worse shock absorber."  One mechanism, split
    # across two layers — so loading it heavily into one is evidence against
    # loading it heavily into the other.  Negative by construction.
    ("phi_R", "kappa_R"): -0.35,
    ("kappa_R", "phi_R"): -0.35,

    # Assumption 7.3 keeps G_pol out of κ_sys to avoid a third coefficient on
    # one capability, because "giving it a third coefficient here would make the
    # three jointly unidentifiable from any data we have".  The two that remain
    # are the same capability read twice and are not separately identified
    # either; this entry states the dependence instead of pretending to it.
    ("phi_G", "gam_G"): 0.30,
    ("gam_G", "phi_G"): 0.30,

    # Table 11.6.  The composite σ_sys performs worse against the dollar than
    # its own friction component, and p_GPRD loads −0.24 on the factor the other
    # legs share.  The news leg and the funding leg are substitutes inside the
    # composite, not complements: weight given to one is weight taken from the
    # thing that actually regresses.
    ("w_F", "w_X"): -0.40,
    ("w_X", "w_F"): -0.40,

    # §10.7.4, the narrative shock, moves both at once and nothing else at all:
    # κ_sys 1.22 → 1.95 and k_Ψ 6 → 28, with no demand or supply channel
    # touched.  The grip of the narrative layer on the reflexive layer and on
    # the secular one is a single grip.
    ("k_psi", "a_H"): 0.50,

    # Both OPEN, both in E8, one series between them.  A deep floor and a late
    # threshold make the same claim about inertia twice, so the data that could
    # move one must move the other against it.  This entry is an identification
    # fact, not an economic one, and it is labelled as such in the UI.
    ("L_max", "theta_0"): -0.30,
    ("theta_0", "L_max"): -0.30,

    # Assumption 2.4 makes the haven term additively separable from the
    # mechanical block in logs, and §10.7 is where the book says that assumption
    # is examined rather than established.  α_prec and λ_1 are rival
    # parameterisations of one flight-to-quality flow: whichever carries it, the
    # other is carrying less.
    ("alpha_prec", "lam_1"): -0.25,
    ("lam_1", "alpha_prec"): -0.25,
}


# --------------------------------------------------------------------------- #
# E17 / E18 — the solved weight state
# --------------------------------------------------------------------------- #

@dataclass
class WeightSolution:
    values: Dict[str, float]          # w_k after interaction
    base: Dict[str, float]            # w_k^0, for comparison
    position: Dict[str, float]        # u_k in (0,1): where in its zone it sits
    drive: Dict[str, float]           # the total logit argument, per weight
    coupling_norm: float              # max_k Σ_j |C_kj|
    unique: bool                      # coupling_norm < 4  (E19)
    amplification: float              # 1/(1 − coupling_norm/4)
    iterations: int
    converged: bool

    def moved(self, rel: float = 0.02) -> List[Tuple[str, float, float, float]]:
        """Weights the interaction law actually moved, largest first."""
        out = []
        for k, v in self.values.items():
            b = self.base[k]
            denom = abs(b) if abs(b) > 1e-12 else 1.0
            d = (v - b) / denom
            if abs(d) >= rel:
                out.append((k, b, v, d))
        out.sort(key=lambda r: -abs(r[3]))
        return out


def solve_weights(
    z: Dict[str, float],
    overrides: Optional[Dict[str, float]] = None,
    coupling: Optional[Dict[Tuple[str, str], float]] = None,
    weights: Optional[Dict[str, Weight]] = None,
    enable_state: bool = True,
    enable_coupling: bool = True,
    tol: float = 1e-13,
    max_iter: int = 500,
) -> WeightSolution:
    """E17 + E18 — solve the weight system.

        E17 (bounded weight map, in departures from the baseline state)
            w_k(z, u) = lo_k + (hi_k − lo_k)·Λ(d_k)
            d_k = ℓ_k + Σ_m γ_km·(z_m − z⁰_m)
                      + Σ_{m,n} Γ_k,mn·(z_m − z⁰_m)(z_n − z⁰_n)
                      + Σ_{j≠k} C_kj·(u_j − u_j⁰)
            ℓ_k = logit(u_k⁰),   u_k⁰ = (w_k⁰ − lo_k)/(hi_k − lo_k)

        E18 (the simultaneity)
            u = Λ(ℓ + Γ(z − z⁰) + C(u − u⁰))

    Properties, all of them inherited from the fact that Λ' ≤ ¼:

      P1  w_k ∈ (lo_k, hi_k) for every z and every C.  Bounds are structural.
      P2  γ = Γ = C = 0  ⟹  w_k ≡ w_k⁰.  E9 is nested exactly.
      P2′ z = z⁰ ⟹ w_k ≡ w_k⁰ whatever γ and Γ are.  The book's stated
          parameter set keeps its meaning at the state Table 10.3 states it for.
      P3  ∂w_k/∂z_m = (hi−lo)·Λ(1−Λ)·(γ_km + Σ_n Γ_k,mn(z_n − z⁰_n)) —
          diminishing at both extremes, the same comparative-static shape E6
          carries in §7.7.5.

    One behaviour worth knowing before it surprises you: a weight whose base is
    pushed hard against its own zone boundary has ℓ_k near ±∞ and is effectively
    frozen — no interaction term can move it.  That is correct rather than a
    defect (it is already at the bound the book imposed), but it means a slider
    pinned at the end of its range switches that weight's interactions off.

    E19 (existence and uniqueness of the weight state).  The map
    u ↦ Λ(ℓ + Γ(z) + C(u − u⁰)) sends the compact convex cube [0,1]^K into
    (0,1)^K continuously, so a fixed point exists UNCONDITIONALLY, by Brouwer —
    the same unconditional existence the book proves for Layer 4 in
    Proposition 8.1.  Its Jacobian has entries Λ'(d_k)·C_kj, bounded by |C_kj|/4,
    so the sup-norm Lipschitz constant is ¼·max_k Σ_j |C_kj|, and

            max_k Σ_j |C_kj| < 4

    makes it a contraction: the weight state is unique, globally attracting from
    any start, and reached geometrically.  That is Proposition 8.2's bound, in
    the same form, for a different loop — which is the point.  The book's
    hyper-brittleness number 1/(1 − T′) has its counterpart here as
    1/(1 − ‖C‖_∞/4), and it diverges as the weight system approaches the same
    boundary.

    Above the bound the engine still returns an answer and marks `unique =
    False`.  It does not silently pick a branch.
    """
    W = weights or WEIGHTS
    C = (coupling if coupling is not None else DEFAULT_COUPLING) if enable_coupling else {}
    ov = overrides or {}

    keys = list(W.keys())

    # Base positions.  An override replaces w_k^0, so the user's slider sets the
    # base the interaction law then moves, rather than being overwritten by it.
    u0: Dict[str, float] = {}
    base: Dict[str, float] = {}
    for k in keys:
        w = W[k]
        b = ov.get(k, w.base)
        b = min(max(b, w.lo + 1e-12), w.hi - 1e-12)
        base[k] = b
        span = w.span()
        u0[k] = (b - w.lo) / span if span > 0 else 0.5
        u0[k] = min(max(u0[k], 1e-9), 1 - 1e-9)

    ell = {k: logit(u0[k]) for k in keys}

    # The state part of the drive: fixed across the iteration.
    state_drive: Dict[str, float] = {}
    for k in keys:
        w = W[k]
        d = 0.0
        if enable_state:
            for m, g in w.gamma.items():
                d += g * (float(z.get(m, Z_BASELINE.get(m, 0.0))) - Z_BASELINE.get(m, 0.0))
            for (m, n), g in w.gamma2.items():
                dm = float(z.get(m, Z_BASELINE.get(m, 0.0))) - Z_BASELINE.get(m, 0.0)
                dn = float(z.get(n, Z_BASELINE.get(n, 0.0))) - Z_BASELINE.get(n, 0.0)
                d += g * dm * dn
        state_drive[k] = d

    # Coupling rows and the sup-norm that decides uniqueness.
    rows: Dict[str, List[Tuple[str, float]]] = {k: [] for k in keys}
    for (k, j), c in C.items():
        if k in rows and j in u0 and k != j:
            rows[k].append((j, c))
    cnorm = max((sum(abs(c) for _, c in rows[k]) for k in keys), default=0.0)

    # Fixed-point iteration.
    u = dict(u0)
    drive: Dict[str, float] = {}
    converged = False
    it = 0
    for it in range(1, max_iter + 1):
        delta = 0.0
        new_u: Dict[str, float] = {}
        for k in keys:
            d = ell[k] + state_drive[k]
            for j, c in rows[k]:
                d += c * (u[j] - u0[j])
            drive[k] = d
            # Exact nesting: a weight that receives no state term and no
            # coupling term returns its base value bit for bit, rather than
            # base + O(1e-9) from a round trip through logit and Λ.  Weights
            # whose base sits on a zone boundary need this, and the nesting
            # property is worth asserting to machine precision.
            val = u0[k] if abs(d - ell[k]) < 1e-15 else logistic(d)
            delta = max(delta, abs(val - u[k]))
            new_u[k] = val
        u = new_u
        if delta < tol:
            converged = True
            break

    values = {k: (base[k] if abs(u[k] - u0[k]) < 1e-15 else W[k].lo + W[k].span() * u[k])
              for k in keys}

    amp = 1.0 / (1.0 - cnorm / 4.0) if cnorm < 4.0 else float("inf")

    return WeightSolution(
        values=values, base=base, position=u, drive=drive,
        coupling_norm=cnorm, unique=cnorm < 4.0, amplification=amp,
        iterations=it, converged=converged,
    )


# --------------------------------------------------------------------------- #
# E20 — weight shares:  "tỉ lệ các trọng số"
# --------------------------------------------------------------------------- #

@dataclass
class WeightShare:
    key: str
    symbol: str
    block: str
    d_lnDXY: float        # ∂ln DXY / ∂w_k, by central difference
    scaled: float         # the derivative times the weight's own admissible span
    share: float          # |scaled| normalised over all weights, in [0, 1]
    direction: int        # +1, −1 or 0


def weight_shares(
    evaluate,
    z: Dict[str, float],
    overrides: Optional[Dict[str, float]] = None,
    weights: Optional[Dict[str, Weight]] = None,
    eps_frac: float = 0.01,
    blocks: Optional[Iterable[str]] = None,
) -> List[WeightShare]:
    """E20 — the influence share of each weight on the current forecast.

        s_k = |(∂ln DXY/∂w_k)·(hi_k − lo_k)| / Σ_j |(∂ln DXY/∂w_j)·(hi_j − lo_j)|

    Scaling the derivative by the weight's own ADMISSIBLE SPAN is what makes the
    shares comparable.  A raw ∂/∂w is in the units of w, and the weights of this
    model are in six different kinds of unit: an elasticity, a logit
    coefficient, a steepness, a threshold, a loss fraction, a rank weight.
    Multiplying by the span asks one question of all of them — "how much of the
    forecast is this weight's zone responsible for?" — and that question has one
    unit.  It is the same normalisation the book's own Notation convention 3
    applies to variables ("a coefficient on any of them reads as the effect of a
    move across the entire range, which makes coefficients comparable across
    layers"); here it is applied to parameters.

    `evaluate(overrides) -> ln DXY` is any closure; `core.make_evaluator` builds
    the standard one.  Central differences, so a weight sitting at a point where
    the model is locally flat reports flat rather than reporting noise.
    """
    W = weights or WEIGHTS
    ov = dict(overrides or {})
    rows: List[WeightShare] = []

    keyset = [k for k in W if blocks is None or W[k].block in set(blocks)]

    for k in keyset:
        w = W[k]
        base = ov.get(k, w.base)
        span = w.span()
        if span <= 0:
            continue
        h = max(span * eps_frac, 1e-9)
        lo_pt = max(base - h, w.lo + 1e-12)
        hi_pt = min(base + h, w.hi - 1e-12)
        if hi_pt <= lo_pt:
            continue

        a = dict(ov); a[k] = lo_pt
        b = dict(ov); b[k] = hi_pt
        try:
            f_lo, f_hi = evaluate(a), evaluate(b)
        except Exception:
            continue
        if f_lo != f_lo or f_hi != f_hi:      # NaN guard
            continue

        d = (f_hi - f_lo) / (hi_pt - lo_pt)
        scaled = d * span
        rows.append(WeightShare(
            key=k, symbol=w.symbol, block=w.block,
            d_lnDXY=d, scaled=scaled, share=0.0,
            direction=(1 if scaled > 1e-12 else (-1 if scaled < -1e-12 else 0)),
        ))

    total = sum(abs(r.scaled) for r in rows)
    if total > 0:
        for r in rows:
            r.share = abs(r.scaled) / total
    rows.sort(key=lambda r: -r.share)
    return rows


def block_shares(rows: Iterable[WeightShare]) -> Dict[str, float]:
    """Weight shares aggregated to the equation each weight belongs to."""
    out: Dict[str, float] = {}
    for r in rows:
        out[r.block] = out.get(r.block, 0.0) + r.share
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))
