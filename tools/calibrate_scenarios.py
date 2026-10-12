"""Solve the per-scenario channel scale that reproduces the figure the book reports.

Each stylised shock in §10.7 and each episode in Part II comes with a number the
book states.  The engine's scenarios move channels; how far they move is not
stated anywhere, because the book moves them in a script it does not print.  This
tool finds, for each scenario, the single scale exponent s on the channel moves
such that the engine reproduces the stated figure, and prints it so the scenario
definitions can carry it with its target beside it.
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
sys.path.insert(0, ".")

from amr import forecast, run
from amr.scenarios import _baseline

B = _baseline()


def scaled(base_moves, s):
    return {k: math.exp(s * math.log(v)) for k, v in base_moves.items()}


def solve(name, sigma_legs, channel_moves, target_pct, pick=lambda f: f.headline.pct,
          lo=0.01, hi=3.0):
    """Bisect on the channel scale so that `pick` hits `target_pct`."""
    def f_of(s):
        st = B.shock(**sigma_legs, **scaled(channel_moves, s))
        return pick(forecast(B, st))

    a, b = lo, hi
    fa, fb = f_of(a) - target_pct, f_of(b) - target_pct
    if fa * fb > 0:
        print(f"{name:<18} KHÔNG bao được mục tiêu {target_pct:+.2f}%  "
              f"(tại s={lo}: {f_of(a):+.2f}%, tại s={hi}: {f_of(b):+.2f}%)")
        return None
    for _ in range(80):
        m = 0.5 * (a + b)
        fm = f_of(m) - target_pct
        if fa * fm <= 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    s = 0.5 * (a + b)
    st = B.shock(**sigma_legs, **scaled(channel_moves, s))
    fc = forecast(B, st)
    print(f"{name:<18} s = {s:.4f}   DXY {fc.headline}   "
          f"σ {fc.sigma_from:.3f}→{fc.sigma_to:.3f}  κ {fc.kappa_from:.3f}→{fc.kappa_to:.3f}  "
          f"Ψ {fc.psi_from:.4f}→{fc.psi_to:.4f}")
    print(f"{'':<18} khối: " + ", ".join(f"{b_.name} {b_.delta_ln*100:+.2f}%" for b_ in fc.blocks))
    print(f"{'':<18} mức kênh: " +
          ", ".join(f"{k}={v:.4f}" for k, v in sorted(scaled(channel_moves, s).items())))
    return s


print("Nền:", {k: round(v, 4) for k, v in [
    ("sigma", run(B).sigma.sigma), ("Phi", run(B).phi), ("s_US", run(B).s_us),
    ("f_hard", run(B).f_hard), ("kappa", run(B).kappa.kappa),
    ("k_psi", run(B).k_psi), ("Psi", run(B).psi_str)]})
print()

solve("liquidity",
      dict(p_vix=0.86, p_bondvol=0.82, p_stlfsi=0.60, p_gpr=0.34),
      dict(bank=0.82, prec=1.55, debt=1.18, cap=0.88, coll=0.90),
      17.7)

solve("sanctions",
      dict(p_gpr=0.72, S_off=0.55, T_frag=0.40),
      dict(ext=0.80),
      4.75)

solve("trust",
      dict(M_trust=0.42, R_US=0.52, E_inf=0.52, p_vix=0.62, p_stlfsi=0.55),
      dict(res=0.90, cap=0.88),
      -4.3)

solve("gfc2008",
      dict(p_vix=0.99, p_bondvol=0.95, p_stlfsi=0.98, p_gpr=0.35),
      dict(prec=1.70, debt=1.30, bank=0.70, coll=0.72, cap=0.80, fed=1.35, swap=3.10),
      6.59)

solve("covid2020",
      dict(p_vix=1.00, p_bondvol=0.93, p_stlfsi=0.90),
      dict(prec=1.60, debt=1.22, bank=0.80, coll=0.78, trans=0.82, fed=1.55, swap=4.00),
      1.85)

solve("rally2022",
      dict(p_vix=0.70, p_bondvol=0.82, p_stlfsi=0.62, p_gpr=1.00,
           S_off=0.50, T_frag=0.42, E_inf=0.70),
      dict(cap=1.25, debt=1.15, fed=0.82),
      15.45)
