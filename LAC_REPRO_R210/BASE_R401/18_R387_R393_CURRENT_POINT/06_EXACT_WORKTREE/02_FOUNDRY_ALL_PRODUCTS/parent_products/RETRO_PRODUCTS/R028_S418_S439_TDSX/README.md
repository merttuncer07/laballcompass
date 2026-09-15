# TDSX v0.1 — Tipping-Distance and Sensitivity-surface Explorer

TDSX evaluates any finite black-box decision metric over declared assumption grids. It reports the
full metric range, share of the surface preserving the baseline decision, nearest normalized decision
flip, and one-parameter-at-a-time tipping values. If no flip exists inside the declared surface, it
says so without extrapolating one.

It also provides an analytic common-value missing-mean tipping calculation and the risk-ratio
confounding E-value. TDSX is a standalone robustness-margin and assumption-design product and does not
require integration with current products.

Run:

```powershell
python -m unittest -v test_tdsx.py
python demo_tipping_surface.py
```
