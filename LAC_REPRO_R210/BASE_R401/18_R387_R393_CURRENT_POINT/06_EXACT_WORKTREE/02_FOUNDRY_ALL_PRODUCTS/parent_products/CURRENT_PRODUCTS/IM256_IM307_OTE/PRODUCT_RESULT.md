# IM-256 → IM-307 product result: Orthogonal Target Estimator v0.1

OTE uses a compact target-relevant representation to estimate nuisance functions, then solves a
cross-fitted orthogonal score so small nuisance errors do not enter the target score at first order.

## Construction result

In 20,000 observations with a true target coefficient of 2.0 and representation-driven confounding:

| Estimator | Estimate | Absolute error |
|---|---:|---:|
| Unadjusted target | 2.104015 | 0.104015 |
| Orthogonal cross-fit | **2.001686** | **0.001686** |

The OTE standard error was 0.007052 and its 95% interval was `[1.987864, 2.015507]`. Residual
treatment variance was 0.9926, so the target retained usable identifying variation in this shell.

Perturbing both nuisance predictions by magnitudes 0.05, 0.10, and 0.20 moved the target along a
roughly quadratic path, consistent with first-order cancellation rather than direct first-order
error transmission.

## Working software

- compact representation input;
- cross-fitted ridge nuisance estimation;
- orthogonal residual target score;
- standard error and confidence interval;
- residual-variation diagnostic;
- explicit rejection when no residual treatment variation remains;
- three automated tests, all passing.

## Next construction layer

Add nonlinear nuisance learners, time/cluster-aware sample splitting, and IM-274 support checks so
the engine refuses targets in unsupported action/population regions rather than forcing an estimate.
