"""
functions.py — The book has exactly one S-shape.  This module holds it.

§10.4: "The logistic appears four times — in sigma_sys, in s_US,sys, in H_soc and
in Psi_str(t) — and each time for the same reason: a quantity that must be
bounded, monotone in a drive, and least responsive at its extremes."

Layer W adds a fifth use and no new functional form.  That is deliberate: the
weight-interaction law of E17 is built out of the same logistic, so a reader who
understands one of the five understands the shape of all of them, and the
"one S-shape" economy of §8.3.3 survives the extension.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

# Guard for the logistic argument.  exp(710) overflows float64; 700 is the
# largest safe magnitude and is far outside any admissible parameter region.
_CLIP = 700.0


def logistic(z: float) -> float:
    """Λ(z) = 1 / (1 + e^-z).  Strictly in (0, 1); never attains its bounds."""
    if z >= 0:
        if z > _CLIP:
            return 1.0 - 1e-300
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    if z < -_CLIP:
        return 1e-300
    ez = math.exp(z)
    return ez / (1.0 + ez)


def logit(u: float) -> float:
    """Inverse of `logistic`, clipped so the open interval is respected."""
    u = min(max(u, 1e-12), 1.0 - 1e-12)
    return math.log(u / (1.0 - u))


def dlogistic(z: float) -> float:
    """Λ'(z) = Λ(1 − Λ).  Maximum 1/4 at z = 0 — the constant behind every
    uniqueness bound in this model, the book's Proposition 8.2 included."""
    lam = logistic(z)
    return lam * (1.0 - lam)


def regime_weight(sigma: float, sigma_star: float, theta: float) -> float:
    """E2.11 — Λ(σ_sys), the shared regime logistic.

    Steepness θ and threshold σ* are shared across all seventeen elasticities:
    'regimes are a property of the system, not of each channel separately.
    Every channel switches at the same time, by different amounts.' (§2.5.2)
    """
    return logistic(theta * (sigma - sigma_star))


def blend(calm: float, crisis: float, lam: float) -> float:
    """E2.9 / E2.10 — x(σ) = x_calm + (x_crisis − x_calm)·Λ(σ)."""
    return calm + (crisis - calm) * lam


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return min(max(x, lo), hi)


def emergent(x: float, x_bar: float) -> float:
    """ISSUES #29 — a channel absent at the base period contributes exactly 1,
    not 0, so the multiplicative aggregate is not destroyed by its absence."""
    if x_bar <= 0:
        return 1.0
    return 1.0 + x / x_bar


def safe_log(x: float, floor: float = 1e-12) -> float:
    return math.log(max(x, floor))


def mean(xs: Iterable[float]) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def percentile_rank(x: float, sample: Sequence[float]) -> float:
    """Assumption 5.1 — every input to E3 enters as its empirical percentile rank.

    Non-negative by construction, which is what the multiplicative friction term
    (1 + w_F F_liq) requires and what a z-score cannot supply.
    """
    if not sample:
        return 0.5
    below = sum(1 for s in sample if s < x)
    equal = sum(1 for s in sample if s == x)
    return (below + 0.5 * equal) / len(sample)
