"""
sensitivity.py — the adjustable zone: feasibility, tornado, and variance shares.

Three questions this module answers, in the order a user asks them.

  1. Is this parameter set ADMISSIBLE?  The monograph's bounds are not
     decoration: κ_R ≥ 1 inverts the model, Φ_sys ≤ 0 flips the sign of the whole
     safe-haven term, ηκ_A g_1 ≥ 4 means the engine is standing on one of three
     branches without saying which.  §10.7 says Chapter 10 "must check" these.
     `feasibility` checks them and reports the slack on each.

  2. Which weight moves the forecast most, across its OWN zone?  That is the
     tornado, and it is the local version of the question.

  3. Across the whole admissible hyper-rectangle, how much of the forecast's
     variance does each weight carry?  That is the global version, and it is the
     one that matters when 42 of 55 parameters are OPEN.  A weight with a wide
     zone and a small derivative can dominate a weight with a narrow zone and a
     large one.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from .core import Options, Result, WorldState, make_evaluator, run
from .registry import WEIGHTS, Weight
from .weightlayer import DEFAULT_COUPLING, solve_weights


# --------------------------------------------------------------------------- #
# 1 — feasibility
# --------------------------------------------------------------------------- #

@dataclass
class Check:
    key: str
    label_vi: str
    ok: bool
    value: float
    bound: str
    slack: float
    source: str


def feasibility(res: Result) -> List[Check]:
    """Every structural constraint the book imposes, with its slack."""
    W = res.weights.values
    out: List[Check] = []

    out.append(Check("kappa_R", "κ_R < 1 (κ_sys > 0)", W["kappa_R"] < 1.0,
                     W["kappa_R"], "< 1", 1.0 - W["kappa_R"], "Assumption 7.2"))

    out.append(Check("phi_pos", "Φ_sys > 0 (không đổi dấu số hạng trú ẩn)",
                     res.phi > 0, res.phi, "> 0", res.phi, "Assumption 2.5 / §6.6.5"))

    out.append(Check("contraction", "η·κ_A·g₁ < 4 (điểm bất động Layer 4 duy nhất)",
                     res.psycho.contraction < 4.0, res.psycho.contraction, "< 4",
                     4.0 - res.psycho.contraction, "Proposition 8.2"))

    g = res.psycho.g0 + res.psycho.g1
    out.append(Check("admissible_g", "g₀ + g₁ ≤ 1 (I_imp ∈ [0,1])", g <= 1.0 + 1e-9,
                     g, "≤ 1", 1.0 - g, "Assumption 8.3"))

    cn = res.weights.coupling_norm
    out.append(Check("weight_contraction", "max_k Σ_j |C_kj| < 4 (hệ trọng số duy nhất)",
                     cn < 4.0, cn, "< 4", 4.0 - cn, "E19 — bổ sung"))

    out.append(Check("sigma_bounds", "σ_sys ∈ [0,1]",
                     0.0 <= res.sigma.sigma <= 1.0, res.sigma.sigma, "∈ [0,1]",
                     min(res.sigma.sigma, 1.0 - res.sigma.sigma), "ISSUES #9"))

    psi_min = 1.0 - W["L_max"]
    out.append(Check("psi_floor", f"Ψ_str ∈ [{psi_min:.3f}, 1]",
                     psi_min - 1e-9 <= res.psi_str <= 1.0 + 1e-9, res.psi_str,
                     f"≥ {psi_min:.3f}", res.psi_str - psi_min, "ISSUES #14"))

    smile = W["lam_1"] < 0 < W["lam_2"]
    out.append(Check("smile", "λ₁ < 0 < λ₂ (điều kiện có nụ cười đô la)", smile,
                     W["lam_1"], "λ₁ < 0", -W["lam_1"], "Proposition 10.3"))

    # The one the book flags hardest about the stated set: the mechanical block
    # multiplied by κ ≈ 1.5 produced a peak a quarter larger than anything the
    # dollar has ever done.
    out.append(Check("kappa_scale", "κ_sys trong dải đã chạy của sách (1,2–2,0)",
                     1.0 <= res.kappa.kappa <= 2.2, res.kappa.kappa, "∈ [1,0; 2,2]",
                     min(res.kappa.kappa - 1.0, 2.2 - res.kappa.kappa), "Table 10.3 / §10.7.5"))

    return out


def feasible(res: Result, ignore: Sequence[str] = ("smile", "kappa_scale")) -> bool:
    """True when every HARD constraint holds.  `smile` is excluded by default
    because the book's own stated set violates it (λ₁ = +0.08 > 0) and that is
    Proposition 10.3 rather than an error; `kappa_scale` is a sanity band, not a
    constraint."""
    return all(c.ok for c in feasibility(res) if c.key not in ignore)


# --------------------------------------------------------------------------- #
# 2 — tornado: the local answer
# --------------------------------------------------------------------------- #

@dataclass
class TornadoBar:
    key: str
    symbol: str
    block: str
    at_lo: float
    at_hi: float
    swing: float          # ln DXY at hi minus at lo, across the full zone
    share: float


def tornado(
    state: Optional[WorldState] = None,
    opt: Optional[Options] = None,
    overrides: Optional[Dict[str, float]] = None,
    keys: Optional[Sequence[str]] = None,
    margin: float = 0.02,
) -> List[TornadoBar]:
    """Swing the forecast over each weight's FULL admissible zone, one at a time.

    This is the direct reading of "vùng tuỳ biến": not a derivative at a point
    but the whole range the parameter is allowed to take, which is the right
    question when the parameter has never been estimated.  `margin` keeps the
    evaluation just inside the open interval.
    """
    ev = make_evaluator(state, opt, overrides)
    ks = list(keys) if keys else list(WEIGHTS.keys())
    bars: List[TornadoBar] = []
    for k in ks:
        w = WEIGHTS[k]
        span = w.span()
        if span <= 0:
            continue
        lo = w.lo + margin * span
        hi = w.hi - margin * span
        try:
            a, b = ev({k: lo}), ev({k: hi})
        except Exception:
            continue
        if a != a or b != b:
            continue
        bars.append(TornadoBar(k, w.symbol, w.block, a, b, b - a, 0.0))

    tot = sum(abs(x.swing) for x in bars) or 1.0
    for x in bars:
        x.share = abs(x.swing) / tot
    bars.sort(key=lambda x: -abs(x.swing))
    return bars


# --------------------------------------------------------------------------- #
# 3 — variance shares over the whole zone: the global answer
# --------------------------------------------------------------------------- #

@dataclass
class VarianceShare:
    key: str
    symbol: str
    block: str
    first_order: float     # S_i, the fraction of output variance this weight alone carries
    correlation: float     # sign and strength of its monotone relation to the output


@dataclass
class MonteCarlo:
    n: int
    mean: float
    sd: float
    q05: float
    q50: float
    q95: float
    feasible_fraction: float
    shares: List[VarianceShare]


def monte_carlo(
    state: Optional[WorldState] = None,
    opt: Optional[Options] = None,
    n: int = 2000,
    keys: Optional[Sequence[str]] = None,
    bins: int = 12,
    seed: int = 20260906,
    drop_infeasible: bool = True,
) -> MonteCarlo:
    """Sample the admissible hyper-rectangle and decompose the output variance.

        S_i = Var_x_i( E[Y | x_i] ) / Var(Y)

    estimated by binning on each weight in turn — the standard one-way
    conditional-variance estimator.  It is a FIRST-ORDER index: with the
    coupling matrix on, weights interact, so the S_i will not sum to one and the
    shortfall is itself informative.  It measures how much of the forecast's
    variability lives in the interactions rather than in any single weight —
    which is the quantity the monograph has no way of reporting at all, because
    its weights are constants.

    `drop_infeasible` discards draws that violate a hard constraint, so the
    reported distribution is over the ADMISSIBLE zone rather than the box.
    """
    rng = random.Random(seed)
    st = state or WorldState()
    o = opt or Options()
    ks = list(keys) if keys else [k for k, w in WEIGHTS.items() if w.span() > 0]

    draws: List[Dict[str, float]] = []
    ys: List[float] = []
    n_try = 0
    n_feas = 0
    target = n
    while len(ys) < target and n_try < target * 6:
        n_try += 1
        d = {}
        for k in ks:
            w = WEIGHTS[k]
            d[k] = w.lo + rng.random() * w.span()
        try:
            r = run(st, d, o)
        except Exception:
            continue
        if r.ln_DXY != r.ln_DXY or math.isinf(r.ln_DXY):
            continue
        ok = feasible(r)
        n_feas += 1 if ok else 0
        if drop_infeasible and not ok:
            continue
        draws.append(d)
        ys.append(r.ln_DXY)

    if not ys:
        return MonteCarlo(0, 0, 0, 0, 0, 0, 0.0, [])

    m = sum(ys) / len(ys)
    var = sum((y - m) ** 2 for y in ys) / max(len(ys) - 1, 1)
    sd = math.sqrt(var)
    srt = sorted(ys)

    def q(p: float) -> float:
        i = min(max(int(p * (len(srt) - 1)), 0), len(srt) - 1)
        return srt[i]

    # Bins must be coarse enough for the sample.  A one-way conditional-variance
    # estimator with k bins explains (k−1)/(n−1) of the variance by chance alone,
    # and with forty weights that bias compounds into a Σ S_i far above one.  The
    # bin count is capped against n and the estimate is bias-corrected below
    # (the epsilon-squared correction), so that `interaction_residual` reports
    # the interaction share rather than the estimator's own noise.
    bins = max(3, min(bins, len(ys) // 30))
    bias = (bins - 1) / max(len(ys) - 1, 1)

    shares: List[VarianceShare] = []
    if var > 0:
        for k in ks:
            w = WEIGHTS[k]
            # Conditional means over equal-width bins of this weight.
            buckets: List[List[float]] = [[] for _ in range(bins)]
            for d, y in zip(draws, ys):
                u = (d[k] - w.lo) / w.span()
                b = min(int(u * bins), bins - 1)
                buckets[b].append(y)
            num = 0.0
            tot = 0
            for b in buckets:
                if not b:
                    continue
                mb = sum(b) / len(b)
                num += len(b) * (mb - m) ** 2
                tot += len(b)
            s_raw = (num / tot) / var if tot else 0.0
            s_i = max(0.0, (s_raw - bias) / max(1.0 - bias, 1e-9))

            # Pearson correlation of the weight with the output, for the sign.
            xs = [d[k] for d in draws]
            mx = sum(xs) / len(xs)
            cov = sum((x - mx) * (y - m) for x, y in zip(xs, ys))
            vx = sum((x - mx) ** 2 for x in xs)
            corr = cov / math.sqrt(vx * var * (len(ys) - 1)) if vx > 0 else 0.0
            corr = max(-1.0, min(1.0, corr))

            shares.append(VarianceShare(k, w.symbol, w.block, s_i, corr))

    shares.sort(key=lambda s: -s.first_order)
    return MonteCarlo(
        n=len(ys), mean=m, sd=sd, q05=q(0.05), q50=q(0.50), q95=q(0.95),
        feasible_fraction=(n_feas / n_try if n_try else 0.0), shares=shares,
    )


def interaction_residual(mc: MonteCarlo) -> float:
    """1 − Σ S_i.  How much of the forecast's variability lives in the
    INTERACTIONS between weights rather than in any weight on its own.

    This number has no counterpart in the monograph, where the weights are
    constants and cannot interact.  It is the quantity Layer W exists to make
    visible, and it is the honest answer to "how much does the interaction
    matrix matter?" — which is a question the user, not the author, should get
    to decide the answer to.
    """
    return 1.0 - sum(s.first_order for s in mc.shares)
