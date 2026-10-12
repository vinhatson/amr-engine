---
title: AMR Engine
emoji: 📈
colorFrom: green
colorTo: gray
sdk: static
app_file: index.html
pinned: false
license: apache-2.0
short_description: Six-layer model of the dollar index, and whether shock order leaves a mark
tags:
  - economics
  - macroeconomics
  - exchange-rates
  - hysteresis
  - complex-systems
  - vietnamese
---

# AMR Engine

The dollar index is usually modelled as one equation. This models it as six
interacting layers, and then asks something most models cannot express: fire
two shocks in one order, then in the other, and let both paths end at the
same state. Do you end up in the same place?

In the original model the answer is necessarily yes, and not because of
calibration. Its core layer is a function of the current state and carries
no history, so two paths reaching the same state must produce the same
output. It is not missing a term — it sits in a function class that cannot
represent the hole that stays behind.

One added parameter and no new edges changes that. At tau = 0 the output is
identical to the original to 0.000e+00. Above zero, three quantities go
non-zero — the commutator of two layer operators, the holonomy of a closed
loop, and the residue left after unwinding a shock — and they do not all
move together, which is what makes the question empirical.

## Three panels, nothing to install

- **Regimes** — the six layers and the three-block attribution.
- **Geometry** — the commutator, the holonomy and the residue, measured.
- **Manifold** — all 78 variables as sliders, in 3D, with the two shocks
  firable in either order.

Each panel is a self-contained HTML file with no build step and no network
calls. This Space is the same three files, hosted.

## Read the limits first

The base model is **qualitative**. It gives an arrow scale and a three-block
attribution, not a calibrated point forecast, and `python -m amr audit`
prints every scenario against the book's own figures so the gap is visible
rather than implied. The tautness rule is exact on one sheet and an
approximation on another, and the code says which. The narrative renderer is
Vietnamese-only for now; all structured output is language neutral.

Source, the Python engine, the three test suites and the paper:
<https://github.com/vinhatson/amr-engine>

Licensed Apache-2.0. Cite the paper, not the Space.
