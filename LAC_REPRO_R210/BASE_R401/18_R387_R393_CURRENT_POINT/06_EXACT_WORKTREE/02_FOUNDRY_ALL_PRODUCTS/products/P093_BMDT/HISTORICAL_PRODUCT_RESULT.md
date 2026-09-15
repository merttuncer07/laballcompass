# P093_BMDT — Belief Metric Decision Tipping

**Composition:** MDDC + TDSX

Finds the nearest point on a declared belief-approximation path where a small metric move changes the downstream action.

## Benchmark

Action flips at path fraction 0.50 with L1 distance only 0.030, producing decision regret 0.020.

## Claim boundary

Path-local result; it is not a global adversarial belief radius.

## Verification

6/6 product tests passed.
