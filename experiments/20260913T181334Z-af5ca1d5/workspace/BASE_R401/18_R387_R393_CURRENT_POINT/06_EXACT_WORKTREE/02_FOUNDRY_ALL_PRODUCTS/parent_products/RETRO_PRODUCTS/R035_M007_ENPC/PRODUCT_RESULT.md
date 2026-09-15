# Product Result — ENPC v0.1

**Retro candidate:** R-035 / M-007 with M-216 solvability shell  
**Historical decision:** prior-art collision  
**Product:** Exposure-Neutral Portfolio Constructor  
**Status:** independent working product

ENPC constructs a bounded portfolio under a budget and requested factor exposures. It first checks
whether the constraints are feasible, then optimizes the mean–variance tradeoff and reports exact
exposure residuals, volatility, expected return, and neutral-subspace dimension.

In the first six-asset construction:

- both requested factor exposures were reduced below **7e-18**;
- the largest equality residual was **1.11e-16**;
- the neutral portfolio's worst tested factor-stress return was effectively **0**;
- the unconstrained portfolio's worst factor-stress return was **−28.13%**;
- factor neutrality cost **8.13 percentage points** of nominal expected return in this deliberately
  factor-heavy example.

Four tests pass, including exact neutralization, infeasibility detection, rejection of a non-PSD
covariance matrix, and preservation of the budget in unconstrained mode. This is a standalone risk
construction product; integration with the current 20-product set is not required.

v0.1 uses a static linear factor model and long/short position bounds. The next standalone layer is
transaction costs, turnover, exposure intervals, covariance uncertainty, and multi-period stress.
