# Exposure-Neutral Portfolio Constructor

ENPC reopens the old prior-art-collision route **R-035** as an independent product. Known precedent
removes a novelty claim; it does not remove the need for a working constructor.

The exact inventory grounding is reconstructed as M-007 (nullspace) with M-216 as the infeasibility
obstruction shell. ENPC jointly enforces budget, target factor exposure, and position bounds, checks
linear feasibility before optimization, and then solves a bounded mean-variance problem. It reports
factor residuals, nullspace dimension, expected return, risk, and the explicit cost of neutrality.

## Run

```powershell
python -m unittest -v test_enpc.py
python demo_factor_neutral.py
```

## Boundary

v0.1 is static and assumes known means, covariance, and factor loadings. Next layers are estimation
uncertainty, turnover/cost, gross leverage, scenario factors, dynamic rebalancing, and robust
feasibility rather than pretending exact inputs.
