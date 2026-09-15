# P092_PDAT — Private Decision Accuracy Tipping

**Composition:** DTPR + TDSX

Maps DTPR Laplace score noise to the epsilon at which a binary threshold action reaches a declared correctness target.

## Benchmark

At margin=1 and sensitivity=1, baseline epsilon 0.1 gives correctness 0.5476; the declared 0.90 target first clears on-grid at epsilon 2.0 (Laplace scale 0.50).

## Claim boundary

Exact adapter currently covers one public threshold/two actions and is a utility calculation, not a new privacy theorem.

## Verification

6/6 product tests passed.
