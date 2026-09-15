# SANP v0.1 — Support-Aware Neutral Portfolio

SANP is the first executable Route-C composition. It connects two parents whose contracts are genuinely compatible:

`SACPS(training returns, support mask) -> regularized covariance -> ENPC(expected returns, covariance, factor constraints, bounds)`

The composition adds a capability that neither parent alone provides: a support-aware covariance estimate can be consumed while still enforcing ENPC's exact budget, factor-exposure, and position constraints.

## Public interface

- `construct_support_aware_neutral_portfolio(...)`
- `compare_with_raw_sample_on_fresh_returns(...)`

The covariance-validation segment is allowed to select SACPS shrinkage. Fresh evaluation is deliberately separate so the validation segment is not reused as final evidence.

## Evidence boundary

SANP certifies numerical support compliance, covariance conditioning, and ENPC constraint residuals. It does **not** certify that the supplied support mask is scientifically correct. `benchmark_route_c.py` contains an explicit misspecification case where a wrong support mask passes numerical constraints but worsens fresh risk.
