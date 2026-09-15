# P096_TRIA — Transient-Risk Information Acquisition

**Composition:** DTRM + AICC

Values measurements by how much their Gaussian covariance update reduces DTRM finite-horizon action-flip risk.

## Benchmark

Baseline transient flip index 1.5485. Static AICC chooses no channel, while dynamic-risk routing selects `measure_x2` and reduces the post-measurement index to 0.1543.

## Claim boundary

Channel cost is expressed in the same declared units as flip-index reduction; Gaussian linear update assumptions remain explicit.

## Verification

6/6 product tests passed.
