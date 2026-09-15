# IM-124 → IM-256 product result: Target-Sufficient Reduction Certifier v0.1

TSRC is an executable feature-deletion optimizer and action-preservation certifier. It maximizes
measurement/computation cost saved while bounding the deleted features' total contribution below the
protected distance to the nearest action boundary.

## Construction result

The first protected representation had 12 features: three core variables and nine low-consequence
details. Across 4,000 declared operating points:

| Result | Value |
|---|---:|
| Features before | 12 |
| Features retained | 3 |
| Features deleted | 9 |
| Measurement/computation cost saved | 28.0 |
| Protected action margin | 3.0000 |
| Certified deleted-score error bound | 0.1565 |
| Remaining margin certificate | 2.8435 |
| Maximum observed score change | 0.1023 |
| Observed action changes | **0** |

During construction, an evaluation initially left a declared feature-deviation bound and invalidated
the paper certificate. The engine now rejects such data explicitly. After the shell was correctly
declared, the certified reduction and observed result agreed.

## Working software

- feature-specific target error bounds;
- exact binary deletion optimization through mixed-integer programming;
- measurement/computation savings objective;
- multi-threshold action margins;
- evaluation-time shell enforcement;
- score-change and action-change verification;
- four automated tests, all passing.

## Next construction layer

Support interval-defined input domains directly, nonlinear score remainder bounds, and pairwise
multiclass margins. Then connect TSRC output to IM-256→IM-307 so nuisance error in the retained
representation cancels to first order.
