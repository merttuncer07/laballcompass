# SCE v0.1 — Specification Curve Engine

SCE runs the complete Cartesian product of user-declared outcome variants, treatment definitions,
control sets, and sample rules. Every valid OLS path reports a heteroskedasticity-robust standard
error and confidence interval; invalid or rank-deficient paths remain visible.

The summary exposes estimate range, median, sign stability, and the shares of positive, negative,
and confidence-excluding-zero results. The user remains responsible for declaring which choices are
defensible; SCE prevents one preferred path from impersonating the entire evidence surface.

This is a standalone effect-analysis product for operational, commercial, or scientific data. It
does not require current-product integration.

Run:

```powershell
python -m unittest -v test_sce.py
python demo_specification_curve.py
```
