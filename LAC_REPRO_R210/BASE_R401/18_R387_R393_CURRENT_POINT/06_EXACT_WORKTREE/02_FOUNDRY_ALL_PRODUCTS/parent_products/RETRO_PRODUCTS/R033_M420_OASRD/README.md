# OASRD v0.1 — Operator-Averaging Stabilizer with Residual Diagnostics

OASRD runs declared identity/operator mixing parameters and measures the real fixed-point residual,
state norm, convergence speed, and late contraction ratio. Direct iteration remains in the comparison
set; averaging is selected only when it actually improves the supplied operator.

Failed and divergent runs are preserved. If none converges, OASRD returns the best observed residual
instead of manufacturing a fixed point. This converts the held operator-averaging technique into a
standalone solver stabilization and diagnostic service.

Run `python -m unittest -v test_oasrd.py` and `python demo_averaging.py`.
