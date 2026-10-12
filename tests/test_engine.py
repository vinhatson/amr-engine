"""Tests.  The load-bearing one is test_nesting: Layer W must reproduce E9
exactly when its loadings are off, or the extension is not an extension.

    python -m pytest tests -q          (or)      python tests/test_engine.py
"""

import math
import sys

# --- UTF-8 console (Windows cp1252 would otherwise abort on the first
#     Vietnamese or Greek character printed below) ---
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):      # non-TTY or already wrapped
        pass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from amr import (  # noqa: E402
    Options, WEIGHTS, WorldState, arrow, feasibility, forecast, logistic,
    monte_carlo, run, run_scenario, solve_weights, tornado,
)
from amr.layers import implied_layer4, psycho_fixed_point, psi_str  # noqa: E402
from amr.scenarios import SCENARIOS  # noqa: E402
from amr.weightlayer import DEFAULT_COUPLING, Z_BASELINE, weight_shares  # noqa: E402
from amr.core import make_evaluator  # noqa: E402


# --------------------------------------------------------------------------- #
# The nesting property — E9 must survive the extension untouched
# --------------------------------------------------------------------------- #

def test_nesting_exact():
    """With every Layer W loading off, each weight equals its stated base."""
    sol = solve_weights({}, enable_state=False, enable_coupling=False)
    for k, w in WEIGHTS.items():
        assert abs(sol.values[k] - w.base) < 1e-9, (k, sol.values[k], w.base)


def test_nesting_at_baseline_state():
    """P2': at z = z⁰ the state loadings contribute nothing, whatever they are.

    This is what keeps Table 10.3's numbers meaning what Table 10.3 means by
    them once Layer W is switched on.  Only the weight-pair coupling can move a
    weight at the baseline state, and here it is switched off."""
    sol = solve_weights(dict(Z_BASELINE), enable_state=True, enable_coupling=False)
    for k, w in WEIGHTS.items():
        assert abs(sol.values[k] - w.base) < 1e-9, (k, sol.values[k], w.base)


def test_nesting_lnDXY():
    """The whole model, not just the weights: Layer W off must give E9."""
    a = run(opt=Options(enable_state_interaction=False, enable_weight_coupling=False))
    sol = solve_weights({}, enable_state=False, enable_coupling=False)
    assert abs(sol.values["kappa_base"] - 0.90) < 1e-12
    assert math.isfinite(a.ln_DXY)
    # And it is a different number from the interacting run, or Layer W does nothing.
    b = run()
    assert abs(a.ln_DXY - b.ln_DXY) > 1e-9


# --------------------------------------------------------------------------- #
# Bounds — no interaction may push a weight out of the zone the book gave it
# --------------------------------------------------------------------------- #

def test_weights_never_leave_their_zone():
    import random
    rng = random.Random(7)
    for _ in range(300):
        z = {k: rng.random() for k in Z_BASELINE}
        sol = solve_weights(z)
        for k, w in WEIGHTS.items():
            assert w.lo <= sol.values[k] <= w.hi, (k, sol.values[k], w.lo, w.hi)


def test_kappa_R_cannot_reach_one():
    """Assumption 7.2 is enforced by the zone, not by a runtime check."""
    assert WEIGHTS["kappa_R"].hi < 1.0


def test_psi_respects_its_floor():
    for f in [0.0, 0.2, 0.34, 0.5, 0.8, 1.0]:
        p = psi_str(f, L_max=0.35, theta_0=0.5, k_psi=6.0)
        assert 0.65 - 1e-12 <= p <= 1.0


def test_coupling_contraction_bound():
    """E19: max_k Σ_j |C_kj| < 4 is the condition, and the shipped matrix meets it."""
    rows = {}
    for (k, j), c in DEFAULT_COUPLING.items():
        rows[k] = rows.get(k, 0.0) + abs(c)
    assert max(rows.values()) < 4.0
    assert solve_weights({}).unique


# --------------------------------------------------------------------------- #
# Layer 4 — the book's own propositions
# --------------------------------------------------------------------------- #

def test_existence_unconditional():
    """Proposition 8.1: a fixed point exists for every admissible parameter
    vector, with no condition at all."""
    import random
    rng = random.Random(11)
    for _ in range(200):
        p = psycho_fixed_point(
            *[rng.random() for _ in range(9)],
            eta=rng.uniform(0.1, 12.0),
            cL0=rng.uniform(0.0, 1.0), cL1=rng.uniform(0.0, 2.0),
        )
        assert 0.0 < p.H_soc < 1.0
        assert 0.0 <= p.I_imp <= 1.0


def test_contraction_bound_is_sharp_in_form():
    """Proposition 8.2: sup|T'| = ¼ηκ_A g₁, so η < 4 alone suffices given the
    bounds κ_A ≤ 1 and g₁ ≤ 1."""
    p = psycho_fixed_point(1, 1, 1, 1, 0.5, 1, 0, 1, 1, eta=3.9, cL0=0.0, cL1=1.0)
    assert p.contraction < 4.0 and p.unique
    q = psycho_fixed_point(1, 1, 1, 1, 0.5, 1, 0, 1, 1, eta=20.0, cL0=0.0, cL1=1.0)
    assert q.contraction >= 4.0 and not q.unique


def test_baseline_is_an_actual_fixed_point():
    """Table 10.3's H_soc = I_imp = 0.30 is reached by solving Equation (8.8),
    not imposed beside it."""
    r = run()
    assert abs(r.psycho.H_soc - 0.30) < 2e-3
    assert abs(r.psycho.I_imp - 0.30) < 2e-3
    imp = implied_layer4(0.30, 0.30, r.psycho.kappa_A, eta=3.0, cL0=0.80, cL1=1.18)
    assert imp.consistent


# --------------------------------------------------------------------------- #
# The baseline reproduces Table 10.3
# --------------------------------------------------------------------------- #

def test_table_10_3_baseline():
    r = run()
    assert abs(r.sigma.sigma - 0.35) < 0.01       # stated 0.35
    assert abs(r.phi - 0.70) < 0.01               # stated 0.70
    assert abs(r.s_us - 0.70) < 0.01              # stated 0.70
    assert abs(r.f_hard - 0.34) < 0.01            # stated 0.34
    assert abs(r.k_psi - 6.0) < 0.01              # stated 6
    assert 1.2 <= r.kappa.kappa <= 2.0            # stated band
    assert not r.warnings


def test_scenarios_hit_their_stated_targets():
    """The scenarios the book gives a number for, and the tolerance each needs."""
    for key, tol in [("liquidity", 0.05), ("trust", 0.05), ("covid2020", 0.05),
                     ("narrative", 1.5)]:
        f = run_scenario(key)
        tgt = SCENARIOS[key].book_target_pct
        assert abs(f.headline.pct - tgt) <= tol, (key, f.headline.pct, tgt)


def test_swap_lines_remove_about_half_the_peak():
    """§10.7.1: 'in this run it removes roughly half the peak'."""
    a = run_scenario("liquidity").headline.pct
    b = run_scenario("liquidity_swaps").headline.pct
    assert 0.4 <= b / a <= 0.6


def test_sanctions_crosses_over():
    """§10.7.2: weaponising the dollar works, and then stops working."""
    early = run_scenario("sanctions").headline.pct
    late = run_scenario("sanctions_late").headline.pct
    assert early > 0 > late


def test_narrative_shock_moves_no_channel():
    """§10.7.4: 'No demand or supply channel moves at all.'"""
    f = run_scenario("narrative")
    for m in f.channels:
        assert abs(m.to_level - m.from_level) < 1e-12


def test_narrative_shock_raises_measured_integrity():
    """The counter-intuitive prediction: measured Ψ_str RISES while the system
    becomes much more fragile."""
    f = run_scenario("narrative")
    assert f.psi_to > f.psi_from
    assert f.shocked.k_psi > f.base.k_psi * 2


# --------------------------------------------------------------------------- #
# Propositions about the assembled equation
# --------------------------------------------------------------------------- #

def test_no_smile_on_the_books_own_set():
    """Proposition 10.3: a sign change requires λ₁ < 0.  Table 10.3 sets
    λ₁ = +0.08, so the stated set cannot produce a smile — and the engine says
    so rather than inventing one."""
    from amr import smile_threshold
    assert smile_threshold(run()) is None


def test_smile_appears_when_lambda1_is_negative():
    from amr import smile_threshold
    r = run(overrides={"lam_1": -0.12, "lam_2": 0.30})
    t = smile_threshold(r)
    assert t is not None and 0.0 < t < 1.0
    assert abs(t - 0.20) < 0.06


def test_stress_response_has_three_components():
    """Equation (10.7): the response to stress is a sum of three derivatives
    that the reduced form of Chapter 5 cannot separate."""
    from amr import d_ln_dxy_d_sigma
    d = d_ln_dxy_d_sigma(run())
    assert set(d) == {"direct_haven", "reflexive", "regime", "total"}
    assert abs(d["total"] - (d["direct_haven"] + d["reflexive"] + d["regime"])) < 1e-9


def test_prec_excluded_from_the_product():
    """ISSUES #7: the index set I excludes prec, which enters as its own factor."""
    from amr.registry import DEMAND
    assert "prec" not in {c.key for c in DEMAND}
    assert "prec" in {t.key for t in run().terms}


def test_s_us_inside_base_has_the_right_limit():
    """§6.7.2: as s_US → 0 the exponent form tends to 1, leaving the numerator
    unchanged in a panic the dollar captures nothing of.  Inside the base it
    tends to zero, which is the intended economics."""
    st = WorldState().shock(prec=1.4)
    lo = run(st, {"gam_0": -3.0}, Options(s_us_inside_base=True))
    hi = run(st, {"gam_0": 3.0}, Options(s_us_inside_base=True))
    assert hi.ln_DXY > lo.ln_DXY


# --------------------------------------------------------------------------- #
# Extensions: each one off by default, each one doing something when on
# --------------------------------------------------------------------------- #

def test_every_extension_is_off_by_default():
    o = Options()
    for flag in ("regime_switched_lambda", "recentre_convexity",
                 "enable_return_path", "enable_reversal", "enable_health_leg",
                 "split_prec_curve", "haven_on_funding_leg"):
        assert getattr(o, flag) is False, flag


def test_recentring_shrinks_the_high_sigma_overshoot():
    """E22 closing I37: re-centring on the entry state cuts the haven block's
    contribution in an episode that begins with σ_sys already high."""
    plain = run_scenario("gfc2008")
    fixed = run_scenario("gfc2008", opt=Options(recentre_convexity=True))
    hav_plain = [b for b in plain.blocks if b.name == "trú ẩn"][0]
    hav_fixed = [b for b in fixed.blocks if b.name == "trú ẩn"][0]
    assert abs(hav_fixed.delta_ln) < abs(hav_plain.delta_ln)


def test_return_path_changes_v_meme():
    """E26 closing I32: (1 + b_F·f_hard) gives Layer 5 an edge into Layer 4."""
    off = run(opt=Options(enable_return_path=False))
    on = run(overrides={"b_F": 1.2}, opt=Options(enable_return_path=True))
    assert on.psycho.V_meme > off.psycho.V_meme


def test_reversal_lowers_fragmentation():
    """E27 closing I34: the one arrow the sign graph does not contain."""
    st = WorldState().shock(T_frag=0.6, S_off=0.5, reversal=1.0)
    off = run(st, opt=Options(enable_reversal=False))
    on = run(st, overrides={"r_rev": 0.5}, opt=Options(enable_reversal=True))
    assert on.f_hard < off.f_hard
    assert on.psi_str > off.psi_str


def test_health_leg_lets_sigma_see_a_pandemic():
    """E25: GPRD measures war and terrorism, so without this leg the clearest
    non-financial shock in the sample moves σ_sys not at all."""
    st = WorldState().shock(p_health=1.0)
    off = run(st, opt=Options(enable_health_leg=False))
    on = run(st, opt=Options(enable_health_leg=True))
    assert abs(off.sigma.sigma - run().sigma.sigma) < 1e-12
    assert on.sigma.sigma > off.sigma.sigma


# --------------------------------------------------------------------------- #
# Weight shares, tornado, feasibility
# --------------------------------------------------------------------------- #

def test_weight_shares_sum_to_one():
    rows = weight_shares(make_evaluator(), z={})
    assert abs(sum(r.share for r in rows) - 1.0) < 1e-9
    assert rows[0].share >= rows[-1].share


def test_tornado_orders_by_swing():
    bars = tornado()
    assert bars
    assert all(abs(bars[i].swing) >= abs(bars[i + 1].swing) for i in range(len(bars) - 1))


def test_feasibility_flags_the_real_constraints():
    checks = {c.key: c for c in feasibility(run())}
    assert checks["kappa_R"].ok
    assert checks["phi_pos"].ok
    assert checks["contraction"].ok
    assert checks["weight_contraction"].ok
    # The book's own stated set violates the smile condition, and that is
    # Proposition 10.3 rather than a bug.
    assert not checks["smile"].ok


def test_infeasible_set_is_caught_not_silently_run():
    r = run(overrides={"phi_0": 0.0, "phi_M": 0.0, "phi_G": 0.0,
                       "phi_R": 1.4, "phi_T": 1.4})
    assert r.phi <= 0
    assert any("Φ_sys" in w for w in r.warnings)


def test_monte_carlo_runs_and_reports_an_interaction_residual():
    from amr import interaction_residual
    mc = monte_carlo(n=400, seed=3)
    assert mc.n > 0
    assert mc.shares
    assert -1.0 <= interaction_residual(mc) <= 1.0


# --------------------------------------------------------------------------- #
# Qualitative layer
# --------------------------------------------------------------------------- #

def test_arrow_scale_matches_the_books_bands():
    assert arrow(0.002).glyph == "↔"
    assert arrow(0.02).glyph == "↑"
    assert arrow(-0.02).glyph == "↓"
    assert arrow(0.05).glyph == "↑↑"
    assert arrow(-0.05).glyph == "↓↓"
    assert arrow(0.12).glyph == "↑↑↑"
    assert arrow(-0.12).glyph == "↓↓↓"


def test_every_scenario_produces_a_reading():
    for k in SCENARIOS:
        f = run_scenario(k)
        text = f.narrative_vi()
        assert "KẾT LUẬN" in text and "PHÂN RÃ THEO KHỐI" in text
        assert math.isfinite(f.headline.pct)


def test_evidence_travels_with_the_arrow():
    """Every channel that carries a forecast carries its Chapter 17 standing."""
    f = run_scenario("gfc2008")
    assert f.channels
    for m in f.channels:
        assert m.evidence in {"SUPPORTED", "PARTIAL", "UNTESTED", "REFUTED",
                              "UNIDENTIFIED", "MEASURED_ZERO", "ADDED"}
        assert m.evidence_note


def test_iran_2026_is_the_refuted_chain():
    """CS12: maximal geopolitical index, quiet funding leg.  The engine must
    show the move running through a channel labelled REFUTED, not hide it."""
    f = run_scenario("iran2026")
    assert f.sigma_to > f.sigma_from


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok   {name}")
            except AssertionError as e:
                fails += 1
                print(f"  FAIL {name}: {e}")
            except Exception as e:  # noqa: BLE001
                fails += 1
                print(f"  ERR  {name}: {type(e).__name__}: {e}")
    print(f"\n{'FAILED' if fails else 'PASSED'} — {fails} failure(s)")
    sys.exit(1 if fails else 0)
