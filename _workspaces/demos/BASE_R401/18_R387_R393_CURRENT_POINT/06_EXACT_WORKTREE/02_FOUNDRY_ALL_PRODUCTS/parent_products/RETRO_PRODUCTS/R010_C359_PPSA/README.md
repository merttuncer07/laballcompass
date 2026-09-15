# PPSA v0.1 — Privacy Pipeline Safety Accountant

PPSA distinguishes privacy-consuming raw-data mechanisms from zero-additional-cost processing of an
already private release. It provides basic sequential composition and, when an explicit delta slack
is supplied, the heterogeneous advanced-composition bound, choosing the tighter epsilon result.

The pipeline validator requires every post-processing step to name an earlier parent and rejects any
step that claims post-processing immunity while accessing raw data. Reports list charged and zero-cost
release IDs, budget utilization, and pass/fail status.

PPSA is a standalone privacy engineering product and needs no integration with current products.

Run:

```powershell
python -m unittest -v test_ppsa.py
python demo_privacy_pipeline.py
```
