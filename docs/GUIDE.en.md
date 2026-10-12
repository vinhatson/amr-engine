# AMR Engine — Full Guide

Everything you need to run the three packages, read what they say, and know
what not to claim. The short version is the [README](../README.md).

**Contents**

1. [Which package do you want?](#1-which-package-do-you-want)
2. [Install](#2-install)
3. [The panels — start here](#3-the-panels--start-here)
4. [`amr` — the book's model](#4-amr--the-books-model)
5. [`amr2` — the corrected model](#5-amr2--the-corrected-model)
6. [`amr3` — the geometric reading](#6-amr3--the-geometric-reading)
7. [The three measurements](#7-the-three-measurements)
8. [Hysteresis vs fatigue](#8-hysteresis-vs-fatigue)
9. [Tests](#9-tests)
10. [What you may and may not claim](#10-what-you-may-and-may-not-claim)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Which package do you want?

Three packages, three different things. Pick by what you want to do.

| you want to… | use | why |
|---|---|---|
| explore the model interactively | **the panels** | no install, runs in a browser |
| read the book's model as code | **`amr`** | six layers at standard form |
| see it fitted to real data | **`amr2`** | FRED panel, OLS/HAC, out-of-sample |
| ask whether shock order matters | **`amr3`** | sheets, scars, path dependence |

The relationship between them is the interesting part:

- **`amr2` deliberately does not import `amr`.** It is a *different* model — the
  book's errors corrected — and it has to stand on its own to be comparable.
- **`amr3` deliberately does import `amr`, and runs it inside itself.** It is
  the *same* model in different coordinates, and the way you prove a re-reading
  is faithful is to run the original inside it.

`amr3` is not a third model. It is `amr`, with all 78 variables unchanged,
re-sorted by **geometric position** instead of by which equation they are a
coefficient of.

---

## 2. Install

Python 3.9 or newer. **No dependencies** — standard library only, for all three
packages.

```bash
git clone https://github.com/<your-username>/amr-engine.git
cd amr-engine
python -m amr check
```

`amr2`'s regression work needs nothing extra either. The FRED series are
vendored in [`data/series.py`](../data/series.py), retrieved 2026-10-09.

### Windows note

Nothing special is needed. The entry points set their own stdout to UTF-8, so a
default console renders the Vietnamese and Greek correctly rather than aborting
on the first such character.

### Important: run from the repository root

`amr3` imports `amr`, and `amr2` loads `data/series.py` relative to the
repository root. Run commands from the top of the clone, not from inside a
package directory.

---

## 3. The panels — start here

Three self-contained HTML pages in [`panels/`](../panels/). No Python, no
server, no build step. Download the repository and open any of them in a
browser, or host them on GitHub Pages.

| panel | what it does |
|---|---|
| `regimes_panel.html` | drive the six layers directly; the three-block decomposition responds live |
| `geometry_panel.html` | the 78 variables placed by geometric role rather than by equation |
| `manifold_panel.html` | the sheets in 3D; fire two shocks in either order and see whether a scar is left |

They load `three.js` and a webfont from a CDN, so the first paint needs a
network connection. Everything else — the model, the registry, the vectors — is
baked into the file.

`manifold_panel.html` is the one to open if you only open one. It has all 78
variables as sliders grouped by sheet (Σ₀ mechanical, Σ₁ state, Σ₂ structural,
and so on), a `Table 10.3` preset, a knife you can open and close, and a toggle
between the two memory models. It is the argument of this project made
touchable.

### Serving them locally

Opening the file directly works. If you would rather serve them:

```bash
cd panels
python -m http.server 8901
# → http://127.0.0.1:8901/manifold_panel.html
```

The panel UI is in Vietnamese. The variable names, the Greek symbols and the
numbers are not language-specific, so the panels are navigable either way —
each sheet group is labelled `Σ₀` … `Σ₅`.

---

## 4. `amr` — the book's model

A runnable implementation of *The Architecture of Market Regimes* (Vi Nhật Sơn,
2026): all six layers in their canonical post-ISSUES form, with boundary checks,
plus a transverse Layer W for the weights.

### The commands

```bash
python -m amr list                 # the scenarios, and what the book says about each
python -m amr run sanctions        # run one scenario, print the qualitative reading
python -m amr run narrative --json # same result as JSON
python -m amr weights              # weight ratios at the baseline state
python -m amr tornado --top 20     # the customisation region: swing across the full range
python -m amr mc --n 1500          # variance decomposition over the feasible region
python -m amr check                # structural constraints, with the slack on each
python -m amr audit                # every scenario against the book's own numbers
```

### The scenarios

Eleven, named:

```
liquidity   liquidity_swaps   sanctions   sanctions_late   trust
narrative   gfc2008   covid2020   rally2022   tariff2025   iran2026
```

The last five are historical case studies (CS1, CS2, CS5, CS11, CS12). Use
`python -m amr list` to see what the book claims about each — the listing prints
the book's own stated outcome next to the scenario, which is what makes `audit`
meaningful.

### The extension flags

These are **global** flags and go **before** the subcommand:

```bash
python -m amr --recentre run narrative        # correct
python -m amr run narrative --recentre        # error: unrecognized arguments
```

| flag | what it turns on |
|---|---|
| `--no-state` | **off**: weight state-dependence (E17) |
| `--no-coupling` | **off**: weight coupling (E18) |
| `--recentre` | convexity re-centring (E22, closes I37) |
| `--regime-lambda` | regime-switching λ₁ (E21, Remark 11.3) |
| `--return-path` | the Layer 5 → Layer 4 return path (E26, closes I32) |
| `--reversal` | the coercive reversal channel (E27, closes I34) |
| `--health-leg` | the non-military exogenous shock leg (E25) |
| `--split-prec` | split `D_prec` along the curve (E28, closes I40) |
| `--funding-haven` | run the haven term off the funding leg |

Every extension is **off by default**. With Layer W's loadings at zero the
engine reproduces E9 exactly, to machine precision — that is a tested property,
not a claim.

### From Python

```python
from amr import WorldState, Options, forecast, run_scenario

f = run_scenario("sanctions")
print(f.narrative_vi())

base  = WorldState()
shock = base.shock(p_vix=0.95, p_stlfsi=0.80, bank=0.94, prec=1.10)
g = forecast(base, shock)

# language-neutral structured output
print(g.blocks)           # three-block attribution with shares
print(g.channels)         # only the channels that actually moved
print(g.evidence_mix)     # Chapter 17 evidential standing, as shares
print(g.sigma_response)   # direct_haven / reflexive / regime / total

# turn on an extension
print(run_scenario("gfc2008", opt=Options(recentre_convexity=True)).narrative_vi())
```

### How to read a reading

```
CONCLUSION: DXY ↑ +2.83%  (small move, within the usual range)
Regime: CALM — below σ*: elasticities at their calm values
σ_sys 0.349 → 0.349   κ_sys 1.460 → 1.460   Ψ_str 0.9022 → 0.8861

BLOCK DECOMPOSITION (Figure 10.2):
  mechanical ×κ      ↑↑ +4.79%    70.9% of absolute total
  haven              ↔ -0.16%      2.4% of absolute total
  structural Ψ       ↓ -1.80%     26.7% of absolute total
  → Dominant block: mechanical ×κ
```

The **block decomposition is the output that matters**, more than the headline
percentage. It tells you *which mechanism* carries the move. A +2.83% that is
71% mechanical is a different claim from a +2.83% that is 71% structural, and
the engine always tells you which you have.

The reading also reports the **evidential standing** of every channel the
forecast ran through (Chapter 17): `UNTESTED`, `PARTIAL` and so on, as shares.
A forecast carried mostly by `UNTESTED` channels is a hypothesis, and the engine
says so rather than letting the decimal places imply otherwise.

### A note on language

**The rendered narrative is Vietnamese only.** The method is `narrative_vi()`;
there is no `narrative_en()`. What is language-neutral is everything structured
— the numbers, the arrow scale, the block attribution, `blocks`, `channels`,
`evidence_mix`, `sigma_response` — plus the `name_en` field that
[`amr/registry.py`](../amr/registry.py) carries for every channel and variable.

So you can drive the model and read its output in English today using the
structured fields. An English renderer is the single most useful contribution
anyone could make to this repository.

---

## 5. `amr2` — the corrected model

```bash
python -m amr2        # the book model against the corrected model, same exam
```

This is a **different model**, not a refinement: the book's errors corrected,
then fitted to real data. It does not import `amr`, on purpose, so the two can
be compared without one contaminating the other.

### The data

Monthly FRED series, retrieved 2026-10-09, vendored in
[`data/series.py`](../data/series.py):

| series | what it is |
|---|---|
| `TWEXAFEGSMTH` | nominal AFE dollar index, monthly average — **the dependent variable** |
| `GS10` | UST 10-year |
| `IRLTLT01DEM156N` | German 10-year government bond |
| `POILBREUSDM` | Brent, USD/barrel |
| `FEDFUNDS` | effective fed funds rate — the **price** leg of `S_Fed` |
| `CPIAUCSL` | CPI-U, to build real rates |

No series is Tier 3, and none was silently substituted.

### One data defect, carried rather than hidden

**CPI for 2025-10 does not exist.** The BLS did not publish it, because of the
federal government shutdown that began 2025-10-01. The value used is a linear
interpolation, and `row.cpi_imputed` is `True` for that month.

This is exactly the class of error the book's own §11.5.2 catches with
`RRPONTSYD` — an empty cell read as a number — so it is flagged rather than
ignored. If you use `amr2`, check `cpi_imputed` before trusting a result that
depends on that month.

### What it reports

Out-of-sample results, not in-sample fit. `tests/test_amr2.py` includes
`test_training_never_touches_2026`, which fails if 2026 data leaks into the
training window. That test existing is the reason the out-of-sample claim is
worth anything.

The repository also ships the backtest scripts used during development
(`backtest_oos.py`, `backtest_hybrid.py`, `backtest_search.py`, and others) in
the original `amr_engine` tree. They are not part of the package API.

---

## 6. `amr3` — the geometric reading

```bash
python -m amr3        # the atlas, the nesting check, three measurements, the τ sweep
```

Same model as `amr`, all 78 variables, re-sorted by geometric position.

### Four roles, not six blocks

`amr` sorts variables by `block = "E4 · Φ_sys"` — an **algebraic** sort,
answering "which formula is this a coefficient of". `amr3` sorts by four roles,
which are four geometrically different things:

| role | what it does | examples |
|---|---|---|
| **position** | moves **the sheet itself** | `θ_0`, `σ*`, `κ_base`, `φ_0` |
| **tangent** | moves **a point on** the sheet | every `α_i`, `β_j`, `φ_G`, `a_V` |
| **curvature** | how much the sheet **bends** | `θ`, `k_Ψ`, `λ_2`, `w_CT` |
| **amplitude** | the sheet's **maximum** excursion | `L_max`, `δ_off` |

There is also `CARRIER` for the variables that carry a price rather than set a
shape.

**All of `amr` lives in the tangent role.** That is why it slides parallel, and
why only the position role can be reached by a puncture: piercing means the
sheet is displaced, not that a point on the sheet is displaced.

`test_atlas_covers_every_amr_variable_exactly_once` asserts 78 of 78 — nothing
added, nothing dropped.

### The seven sheets

```
MECHANICAL   STATE   STRUCTURAL   REFLEXIVE   PSYCHO   SECULAR   HAVEN
```

Σ₄ is the only sheet with **no** position weight, so nothing can pierce back
into it. That is not an oversight — Remark 10.2 of the book says Layer 4 "is a
source… it acts on Layers 3 and 5 and is not acted upon in return."

### Exactly one new parameter

```
τ_{ℓm} ∈ [0,1]     the NORMAL share of the action from sheet ℓ onto sheet m
a = a_∥ + a_⊥      a_∥ = (1−τ)·load,   a_⊥ = τ·load
```

**No edges are added.** The edge set is taken unchanged from the `gamma` field
in `amr/registry.py`, where the cross-layer loadings are already encoded.
Exactly one of those edges has a load of zero, and it is the only edge pointing
at a **position-role** weight: `Σ₄ → Σ₅`, `hsoc → theta_0`. The registry's own
comment reads: *"The loading below is the departure, and it is zero by
default."* The door was built and locked.

```python
from amr3 import Options3, Transversality, Memory

Options3(tv=Transversality.zero())        # τ ≡ 0 — the null, and the default
Options3(tv=Transversality.knife())       # τ = 0.294, the ceiling
Options3(tv=Transversality.knife(0.15))   # any value you like
```

`TAU_CEILING` is `0.294`, and it differs by memory model:

```python
TAU_CEILING_BY_MODE == {"hysteresis": 0.294, "fatigue": 0.122}
```

### Puncture depth is not arbitrary

```
Δξ_m = τ_{ℓm} · p · (src_ℓ − H*_ℓ)₊ · (1 + q · II_m)
II_m = 4 · Λ′(arg_m) ∈ [0,1]
```

The factor of 4 is not a cosmetic normalisation. `Λ′ ≤ ¼` is **the same**
inequality Proposition 8.2 uses to get the contraction bound `ηκ_A g₁ < 4`, and
that Layer W uses to get `max_k Σ_j |C_kj| < 4`. The same ¼ that bounds
contraction also bounds **tautness**: a sheet is tautest exactly where it is
steepest, at the inflection point. Taut paper tears; slack paper drifts.

On Σ₅ the rule is **exact**, not approximate: since
`Ψ_str = 1 − L_max·Λ(k_Ψ(f_hard − θ_0))`, we have `(1−Ψ_str)/L_max = Λ(arg)` by
definition, and `4v(1−v) = 4Λ′(arg)`. **On Σ₁ it is an approximation**, because
`σ_sys` is a linear composite rather than a logistic — and that is said out
loud rather than passed over.

### Monotonicity is everything

`ξ_m(t)` never decreases. Ever. Every irreversibility, every path dependence,
every non-zero commutator comes from that one `≥`. No second mechanism was
added.

### From Python

```python
from amr3 import (Options3, Transversality, Memory, Move, Sheet,
                  trace, commutator, holonomy, residual)
from amr import WorldState

state = WorldState()
opt   = Options3(tv=Transversality.knife(), memory=Memory.HYSTERESIS)

# Options3 fields: tv, fragmentation_feedback, amr, memory
# trace(moves, state, opt, settle)
```

`trace(..., settle=True)` adds one no-op step. You need it: a step's scar is
added **after** that step reads its numbers, so stopping immediately records the
last puncture without any read seeing it, and the commutator would then be
measuring the *moment of reading* rather than only the order. The settle step
puts every path on the same observational convention.

---

## 7. The three measurements

`amr3` measures three quantities that are all **exactly zero** in `amr`:

| | τ ≡ 0 | hysteresis · τ = 0.294 | fatigue · τ = 0.122 |
|---|---|---|---|
| commutator ‖[L₄, L₅]‖ | **0.000e+00** | **0.000e+00** | 1.720e-02 |
| holonomy H(γ) | **+0.000e+00** | **−7.318e-02** | **−4.056e-02** |
| residue after unwinding | **+0.000000** | **+0.027931** | **+0.011078** |

The first column is **not** a calibration result. Layer E9 is a function of
`(D_i, S_j, σ, Φ, κ, Ψ)` and carries no history, so two paths reaching the same
state **must** give the same output. `amr` is not missing a term — it sits in a
**function class** that cannot contain the phenomenon "the hole that stays
behind."

**The commutator splits the two branches exactly.** The hysteresis form takes a
running maximum over history; two orderings traverse the same state set, so the
maxima agree, so the commutator is zero **by the definition of the operator**.
The fatigue form integrates, so order matters. Holonomy and residue are non-zero
in **both**: a closed loop returns to the starting state, and the scar stays.

### The empirical question

This does not need a long sample:

> **Does the order of two shocks change the permanent level, when the final
> state is identical?**
>
> Yes → fatigue. No → hysteresis.

### The invariant is not the dimension count

A two-sheet model that scars is already a puncture; a ten-sheet model that does
not scar is still a slide. The invariant that matters is whether the layer
operators **commute** — and the commutator is algebra, so "geometry rather than
algebra" is a false dichotomy, even though the substance of the claim survives
intact. The repository says this about its own framing rather than overselling
it.

---

## 8. Hysteresis vs fatigue

These are two different **physics**, not two approximations of one thing.

```python
Options3(memory=Memory.HYSTERESIS)   # default — ξ = running MAXIMUM over history
Options3(memory=Memory.FATIGUE)      #           ξ = INTEGRAL over dt
```

**HYSTERESIS** — only the extremes of the path count; duration does not enter
the formula. This is the play/stop operator of hysteresis theory, and the
Baldwin–Krugman (1989) form used for exchange rates specifically. It is the
default because it is the substance of the claim, it is the canonical operator
of the literature, and it is **rate-independent**.

**FATIGUE** — duration can **substitute for** amplitude. Miner's rule from
materials fatigue. It is kept because it makes a **different, falsifiable**
prediction, not because it approximates the other.

| total dt | hysteresis | fatigue |
|---|---|---|
| 1 | 0.132064 | 0.132440 |
| 4 | 0.132064 | 0.200946 |
| 32 | **0.132064** | **0.840335** |

The hysteresis row is absolutely flat. That is not an approximation — duration
is not in the formula.

### Rate independence

Splitting **the same path** into more steps must not change the result. That is
the defining property of any hysteresis operator, and
`test_scar_is_rate_independent_in_both_modes` holds the code to it. Two earlier
bugs broke exactly this and were fixed; the test exists so they cannot come
back.

---

## 9. Tests

```bash
python tests/test_engine.py     # amr   — layers, boundaries, Table 10.3
python tests/test_amr2.py       # amr2  — data integrity, no 2026 leakage
python tests/test_amr3.py       # amr3  — atlas 78/78, nesting at τ→0
```

Run all three from the repository root. All pass on Python 3.12 across Windows,
macOS and Linux.

These suites check **structure**, not just output. A few worth knowing about:

- `test_atlas_covers_every_amr_variable_exactly_once` — 78 of 78
- `test_tau_zero_reproduces_amr_exactly` — the nesting claim
- `test_tau_zero_matches_amr_along_a_whole_path` — nesting along a trajectory,
  not just at a point
- `test_scar_is_monotone_non_decreasing` — the one `≥` everything rests on
- `test_scar_is_rate_independent_in_both_modes` — the hysteresis property
- `test_the_knife_edge_is_the_one_amr_set_to_zero` — the single zero-load edge
- `test_world_state_is_never_mutated_in_place`
- `test_amr2_is_untouched` and `test_amr3_does_not_import_amr2` — the
  independence of the rival model is enforced, not just intended
- `test_training_never_touches_2026` — the out-of-sample guarantee

---

## 10. What you may and may not claim

**`amr` is qualitative.** It produces an arrow scale and a three-block
decomposition, not a calibrated point forecast. `python -m amr audit` runs every
scenario against the book's own figures so the gap is visible rather than
implied.

**You may:**
- report which block dominates a move, and by what share
- report the direction and the arrow-scale magnitude
- report the evidential standing of the channels carrying a result
- report that a result is or is not robust to an extension flag
- report `amr2`'s out-of-sample numbers as out-of-sample numbers
- report the three `amr3` measurements, with the memory model stated

**You may not:**
- quote an `amr` percentage as a calibrated forecast
- quote a result without saying which memory model produced it — hysteresis and
  fatigue are different physics and give different numbers
- quote a τ > 0 result without stating τ, since its default and its null are 0
- treat the Σ₁ tautness rule as exact; it is exact only on Σ₅
- treat the geometric framing as a claim about dimensionality
- use `amr2`'s 2025-10 month without checking `cpi_imputed`

If a conclusion survives both memory models, a sweep of τ, and the extension
flags, you have something structural.

---

## 11. Troubleshooting

**`ModuleNotFoundError: No module named 'amr'`**
You are running from inside a package directory, or `amr3`/`amr2` cannot see the
repository root. Run from the top of the clone.

**`ModuleNotFoundError: No module named 'series'`**
`amr2` loads `data/series.py` relative to the repository root. Make sure
`data/` is present and you are at the top of the clone.

**`amr: error: unrecognized arguments: --recentre`**
The extension flags are global and go **before** the subcommand:
`python -m amr --recentre run narrative`.

**`amr run: error: the following arguments are required: scenario`**
`run` needs a scenario name. `python -m amr list` shows them.

**The 3D panel is blank**
It needs `three.js` from a CDN, so the first load requires a network
connection. If you are offline, download
`https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js` and point
the `<script src=…>` at your local copy. A blank panel with a console error
`THREE is not defined` is exactly this.

**The panel text looks like `Äa táº¡p`**
That is a character-encoding problem, and it should not happen — each panel
declares `<meta charset="utf-8">` in its first bytes. If you see it, the file
has probably been re-saved in a non-UTF-8 encoding by an editor.

**Unicode errors in the console**
Should not happen; the entry points set stdout to UTF-8 themselves. If you hit
one, report your OS, terminal and Python version — and as a workaround set
`PYTHONIOENCODING=utf-8`.

---

## See also

- [README.md](../README.md) — the short version
- [README.vi.md](../README.vi.md) — bản tiếng Việt
- [GUIDE.vi.md](GUIDE.vi.md) — this guide in Vietnamese
- [../SPEC.md](../SPEC.md) — the mathematics in full
- [user-manual-en.pdf](user-manual-en.pdf) — the `amr3` manual
- [amr3-notes-vi.md](amr3-notes-vi.md) / [amr2-notes-vi.md](amr2-notes-vi.md) —
  design notes (Vietnamese), argumentative rather than instructional
- [The_Architecture_of_Market_Regimes_Model.pdf](The_Architecture_of_Market_Regimes_Model.pdf) —
  the source paper
