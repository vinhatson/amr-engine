"""
AMR — a qualitative forecasting engine for "The Architecture of Market Regimes".

Vi Nhat Son, *The Architecture of Market Regimes: Modeling DXY through
Structural and Reflexive Layers* (Expanded and Consolidated Edition, 2026).

The engine implements Layers 0 to 5 in their canonical post-ISSUES form, adds a
transverse Layer W for the weights, and reports in the book's own qualitative
vocabulary — the arrow scale, the three-block attribution of Figure 10.2, and
the Chapter 17 evidential standing of every channel a forecast runs through.

Quick start
-----------
    from amr import WorldState, Options, forecast, run_scenario

    f = run_scenario("sanctions")
    print(f.narrative_vi())

    base = WorldState()
    shocked = base.shock(p_vix=0.95, bank=0.80, prec=1.5)
    print(forecast(base, shocked).narrative_vi())

Everything that departs from the book sits behind a flag in `Options`, and every
one of those flags is off by default.  `tests/test_nesting.py` asserts that with
Layer W's loadings at zero the engine reproduces E9 exactly.
"""

from .core import (  # noqa: F401
    Options, Result, Term, WorldState, d_ln_dxy_d_sigma, elasticities,
    make_evaluator, run, smile_threshold,
)
from .functions import blend, logistic, logit, regime_weight  # noqa: F401
from .layers import (  # noqa: F401
    Crisis, KappaOut, PsychoOut, SigmaInputs, SigmaOut, f_hard_agg, k_psi_fn,
    kappa_sys, m_shock, phi_sys, psi_str, psycho_fixed_point, s_us_sys, sigma_sys,
)
from .qualitative import (  # noqa: F401
    Arrow, BlockAttribution, ChannelMove, Forecast, Regime, arrow,
    classify_regime, forecast, CONVEXITY_NOTE_VI, RESIDUAL_NOTE_VI,
)
from .registry import (  # noqa: F401
    CHANNELS, CONSTRAINTS, DEMAND, D_PREC, Evidence, LATENTS, Layer,
    Provenance, SUPPLY, WEIGHTS, Weight, Z_DRIVERS,
)
from .scenarios import BOOK_SANITY_CHECK, SCENARIOS, run_all, run_scenario  # noqa: F401
from .sensitivity import (  # noqa: F401
    Check, MonteCarlo, TornadoBar, VarianceShare, feasibility, feasible,
    interaction_residual, monte_carlo, tornado,
)
from .weightlayer import (  # noqa: F401
    DEFAULT_COUPLING, WeightShare, WeightSolution, block_shares, solve_weights,
    weight_shares,
)

__version__ = "1.0.0"
__author_of_source_model__ = "Vi Nhật Sơn"
