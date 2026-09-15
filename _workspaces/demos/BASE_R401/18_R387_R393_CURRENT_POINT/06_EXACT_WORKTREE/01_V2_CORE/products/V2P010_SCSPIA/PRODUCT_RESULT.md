# V2P010 SCSPIA — development adapter result

**Composition:** Foundry parent `R037 SACPS` + Foundry `P138 SPIA`

**Name:** Support-Calibrated Search-Policy Information Acquisition

## Neutral primitive

`historical belief samples -> project to sum-preserving tangent coordinates -> enforce declared covariance support + shrinkage -> lift covariance back to simplex -> value measurement channels by downstream search-policy decision improvement`

## Honest interface

P138 SPIA is highly sensitive to the supplied belief covariance because channel value is computed through the covariance-dependent posterior update. Its safety contract enforces the simplex tangent space but does not estimate or regularize covariance. SACPS supplies that missing estimation layer, but ordinary SACPS covariance does not automatically preserve probability-sum geometry. SCSPIA therefore performs SACPS in an orthonormal `(n-1)` tangent basis and lifts the result as `B C B^T`, preserving zero row/column sums exactly up to numerical rounding.

This changes the observable decision: noisy unsupported cross-covariances can alter which information channel SPIA buys. The composition is not a warning wrapper; it changes the covariance passed into SPIA while preserving a declared support mask.

## Contrastive boundary benchmark

A fixed seed-1 synthetic shell uses a diagonal true tangent covariance and only 12 calibration beliefs. The oracle P138 decision selects channel `c6`. P138 with the unconstrained raw sample covariance selects `c1` because small-sample cross-covariances distort channel value. SCSPIA removes unsupported tangent cross-covariances and recovers the oracle `c6` choice. Its absolute error for the oracle channel's net value is also lower than the raw-covariance comparator in this construction.

The true covariance is benchmark-only oracle information and is not supplied to SCSPIA. This is a deterministic synthetic mechanism result, not evidence that diagonal tangent support is appropriate in a real search domain.

## Working region

- Historical belief rows are valid probability vectors.
- A scientifically justified tangent-coordinate support mask is declared.
- The covariance shell is sufficiently stationary for calibration beliefs to inform the current belief.
- P138 policies cover every declared location and channels are zero-sum contrasts.

## Failure / abstention region

- A wrong support mask can suppress real covariance structure.
- Covariance transfer from calibration beliefs to the current search state remains a separate assumption.
- The tangent basis is deterministic but support statements are basis-dependent and must be declared accordingly.
- Deployment requires held-out/domain-native covariance and decision validation.

## Development checks

- 12/12 focused tests pass.
- Lifted covariance satisfies P138's simplex-tangent contract.
- Unsupported covariance entries are exactly zero in the declared tangent basis.
- Mechanism-removing comparator is P138 with raw sample covariance.

**Evidence:** executable small-sample synthetic mechanism result; no production claim.
