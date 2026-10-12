# AMR — The Architecture of Market Regimes

A runnable implementation of *The Architecture of Market Regimes: Modeling DXY
through Structural and Reflexive Layers* (Vi Nhật Sơn, 2026), plus two layers
built on top of it.

**[→ Open the interactive panels in your browser](#interactive-panels-no-install)** ·
**[User manual (EN)](docs/user-manual-en.pdf)** ·
**[Hướng dẫn tiếng Việt](README.vi.md)** ·
**[The paper (PDF)](docs/The_Architecture_of_Market_Regimes_Model.pdf)**

---

## What this is

The dollar index (DXY) is usually modelled as a single equation. This project
models it as **six interacting layers** — mechanical flows, a volatility state,
a structural layer, a reflexive layer, a strategic layer, and a weight layer —
and asks a question most models cannot ask: *does the order in which two shocks
arrive change where you end up?*

Three packages ship here, and they are deliberately different things:

| package | what it is | runs standalone |
|---|---|---|
| **`amr`** | the book's model, six layers at standard form, with boundary checks | yes |
| **`amr2`** | a **different** model — the book's errors corrected, fitted to real FRED data, with out-of-sample backtests | yes, by design does not import `amr` |
| **`amr3`** | the **same** model as `amr`, re-read in geometric coordinates: sheets, scars, path dependence | imports and runs `amr` inside itself |

`amr2` stands apart because it is a rival model and has to be comparable.
`amr3` nests `amr` because it is the same model in different coordinates, and
the way you prove a re-reading is faithful is to run the original inside it:

```
τ ≡ 0  →  no overrides  →  ln DXY identical to amr, difference 0.000e+00
```

---

## Interactive panels (no install)

Three self-contained HTML pages. Download and open in any browser, or host them
on GitHub Pages — no Python, no server, no build step.

| panel | what you can do |
|---|---|
| [`panels/regimes_panel.html`](panels/regimes_panel.html) | drive the six layers directly; watch the three-block decomposition respond |
| [`panels/geometry_panel.html`](panels/geometry_panel.html) | the 78 variables placed by geometric role rather than by equation |
| [`panels/manifold_panel.html`](panels/manifold_panel.html) | the sheets in 3D; fire shocks in either order and see whether a scar is left |

They load `three.js` and a font from a CDN, so first paint needs a connection.
Everything else — the model, the registry, the vectors — is baked into the file.

---

## Install

Python 3.9+. The core has **no dependencies at all** — standard library only.

```bash
git clone https://github.com/vinhatson/amr-engine.git
cd amr-engine
python -m amr check          # structural constraints, with the slack on each
```

`amr2`'s regression work needs nothing extra either; the FRED series are
vendored in [`data/series.py`](data/series.py) as retrieved on 2026-10-09.

---

## Quick start

```bash
python -m amr list                 # the book's scenarios, and what it says about each
python -m amr run narrative        # a full qualitative reading of one episode
python -m amr weights              # weight ratios at the current state
python -m amr tornado              # sweep every weight across its whole range
python -m amr mc --n 1500          # variance decomposition; how much sits in interaction
python -m amr audit                # every scenario against the book's own numbers

python -m amr2                     # book model vs corrected model, same exam
python -m amr3                     # the atlas, three measurements, the τ sweep
```

```python
from amr import WorldState, Options, forecast, run_scenario

f = run_scenario("sanctions")
print(f.narrative_vi())

base  = WorldState()
shock = base.shock(p_vix=0.95, p_stlfsi=0.80, bank=0.94, prec=1.10)
print(forecast(base, shock).narrative_vi())
```

Every command takes the extension flags — and they go **before** the
subcommand, because they are global:

```bash
python -m amr --recentre run narrative        # correct
python -m amr run narrative --recentre        # error: unrecognized arguments
```

The flags are `--recentre`, `--regime-lambda`, `--return-path`, `--reversal`,
`--health-leg`, `--split-prec`, `--funding-haven`, `--no-state`,
`--no-coupling`. Every one is off by default: with Layer W's loadings at zero
the engine reproduces E9 exactly.

### A note on language

**The rendered narrative is currently Vietnamese only** — the method is
`narrative_vi()`, and there is no `narrative_en()` yet. What *is* language
neutral is everything structured, which is most of what you need:

- the numbers (`sigma_from`, `kappa_to`, `psi_to`, elasticities, shares)
- the arrow scale and the three-block attribution
- `Forecast.blocks`, `.channels`, `.evidence_mix`, `.sigma_response`
- channel and variable names, which carry a `name_en` field in
  [`amr/registry.py`](amr/registry.py)

So you can drive the model and read its output in English today by using the
structured fields rather than the rendered paragraph. An English renderer is
the most useful contribution anyone could make here — see
[Contributing](#contributing).

By contrast, the author's other engine
([sccdx-engine](https://github.com/vinhatson/sccdx-engine)) is fully
bilingual, with 406 paired templates and a test that fails if either side is
missing.

---

## The result worth arguing about

`amr3` measures three quantities that are all **exactly zero** in the original
model — not small, zero, and zero for a structural reason:

| | τ ≡ 0 | hysteresis · τ = 0.294 | fatigue · τ = 0.122 |
|---|---|---|---|
| commutator ‖[L₄, L₅]‖ | **0.000e+00** | **0.000e+00** | 1.720e-02 |
| holonomy H(γ) | **+0.000e+00** | **−7.318e-02** | **−4.056e-02** |
| residue after unwinding the shock | **+0.000000** | **+0.027931** | **+0.011078** |

The original model's layer E9 is a function of the current state and carries no
history, so two paths reaching the same state **must** produce the same output.
It is not missing a term — it sits in a *function class* that cannot express
"the hole that stays behind."

That turns into an empirical question which does not need a long sample:

> **Does the order of two shocks change the permanent level, when the final
> state is identical?**
> Yes → fatigue. No → hysteresis.

Note that the hysteresis commutator is zero **by the definition of the
operator** (a running maximum over history: two orders traverse the same state
set, so the maxima agree), while holonomy and residue are non-zero in both. A
closed loop returns to the starting state; the scar remains.

---

## Honest limits

Read these before quoting any number.

- **`amr` is qualitative.** It produces an arrow scale and a three-block
  decomposition, not a calibrated point forecast. `python -m amr audit` shows
  every scenario against the book's own figures so you can see the gap.
- **`amr3` adds exactly one parameter** (`τ`, the normal share of a cross-sheet
  action) and **no new edges** — the edge set is taken unchanged from the
  `gamma` field of `amr/registry.py`. Its default is `0`, which is the null.
- **On Σ₅ the tautness rule is exact; on Σ₁ it is an approximation**, because
  `σ_sys` is a linear composite rather than a logistic. The code says so rather
  than passing over it.
- **`amr2` is where the real data lives**, and it reports out-of-sample results,
  not in-sample fit. One known data defect is carried rather than hidden: CPI
  for 2025-10 does not exist (the BLS did not publish during the federal
  shutdown that began 2025-10-01), so that month is linearly interpolated and
  `row.cpi_imputed` is `True` there.
- **The geometric framing is a reading, not a new dimension count.** A
  two-sheet model that scars is already a puncture; a ten-sheet model that does
  not is still a slide. The invariant that matters is whether the layer
  operators commute.

---

## Repository layout

```
amr/            the book's model — six layers, registry, CLI, sensitivity
amr2/           the corrected model — FRED panel, OLS/HAC, backtests
amr3/           the geometric reading — atlas, sheets, scars, operators
data/series.py  FRED monthly series, retrieved 2026-10-09
panels/         three self-contained interactive HTML pages
docs/           the paper, the manuals (EN/VI), design notes
tests/          three suites; run all three before trusting anything
tools/          scenario calibration helper
SPEC.md         the mathematics, in full
```

---

## Tests

```bash
python tests/test_engine.py     # amr   — layers, boundaries, Table 10.3
python tests/test_amr2.py       # amr2  — data integrity, no 2026 leakage into training
python tests/test_amr3.py       # amr3  — atlas covers 78/78, nesting at τ→0
```

All three pass on Python 3.12 / Windows, macOS and Linux. The suites check
structure, not just output: `test_atlas_covers_every_amr_variable_exactly_once`
asserts 78 of 78, nothing added and nothing dropped.

---

## Documentation

- **[SPEC.md](SPEC.md)** — the mathematics in full
- **[docs/user-manual-en.pdf](docs/user-manual-en.pdf)** — the manual (also [HTML](docs/user-manual-en.html))
- **[docs/huong-dan-su-dung-vi.pdf](docs/huong-dan-su-dung-vi.pdf)** — bản tiếng Việt (also [HTML](docs/huong-dan-su-dung-vi.html))
- **[docs/GUIDE.en.md](docs/GUIDE.en.md)** — full walkthrough, every command explained
- **[docs/GUIDE.vi.md](docs/GUIDE.vi.md)** — hướng dẫn đầy đủ bằng tiếng Việt
- **[docs/The_Architecture_of_Market_Regimes_Model.pdf](docs/The_Architecture_of_Market_Regimes_Model.pdf)** — the source paper

Design notes written during development survive as
[`docs/amr3-notes-vi.md`](docs/amr3-notes-vi.md) and
[`docs/amr2-notes-vi.md`](docs/amr2-notes-vi.md) (Vietnamese). They are
argumentative rather than instructional, and they are worth reading if you want
to know *why* a choice was made.

---

## Contributing

Issues and pull requests are welcome. Two things would help most:

1. **An English narrative renderer** (`narrative_en()`). The template in
   `amr/qualitative.py` is about forty lines; the harder part is the prose that
   lives in `amr/registry.py` and `amr/scenarios.py`. The structured fields are
   already language neutral, so this is a rendering job, not a modelling one.
2. **Disagreement with evidence.** If you can show the order of two shocks does
   *not* change the permanent level when the final state is held fixed, that is
   a result, and it belongs in an issue.

Please keep the test suites green and add a test alongside a behaviour change.

---

## Citation

See [CITATION.cff](CITATION.cff), or:

> Vi Nhật Sơn (2026). *The Architecture of Market Regimes: Modeling DXY through
> Structural and Reflexive Layers.*

---

## License

[Apache License 2.0](LICENSE) — commercial use, modification and distribution
permitted, with a patent grant and a requirement to state your changes. See
[NOTICE](NOTICE) for the terms covering the PDF papers.
