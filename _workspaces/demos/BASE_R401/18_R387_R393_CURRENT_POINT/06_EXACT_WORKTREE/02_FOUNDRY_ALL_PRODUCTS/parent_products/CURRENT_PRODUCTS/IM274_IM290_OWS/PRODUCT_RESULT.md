# IM-274 → IM-290 product result: Overlap-aware Weight Stabilizer v0.1

OWS audits support before transport/reweighting and replaces explosive exact weights with an explicit
bias-variance choice when that improves the declared operating objective.

## Construction result

Across 400 repetitions with source sample size 500 and a two-standard-deviation target shift:

| Result | Value |
|---|---:|
| Raw exact-weight MSE | 0.006439 |
| Stabilized-weight MSE | 0.003956 |
| MSE reduction | **38.56%** |
| Median selected cap | 1.6509 |
| Median effective-sample fraction before stabilization | 6.62% |
| Repetitions flagged `SUPPORT_FRAGILE` | 82.0% |

The first overly conservative objective selected no clipping; a second shell produced slightly worse
MSE. Those outcomes were not hidden. The final engine separates the hard bounded-outcome clipping-
bias bound from an explicit `bias_aversion` weight. In the bounded noisy-outcome shell, the resulting
cap reduced real repeated-sample error while preserving the fragile-support warning.

## Working software

- ESS, maximum-weight, and top-one-percent-mass support audit;
- bounded-outcome shell enforcement;
- transparent cap search;
- hard worst-case clipping-bias bound;
- explicit bias-aversion versus weighted-variance objective;
- raw and stabilized estimates kept side by side;
- four automated tests, all passing.

## Next construction layer

Estimate density ratios with cross-fitting, add action/population-region support maps, and return
partial-identification bounds when support is too weak for a point estimate.
