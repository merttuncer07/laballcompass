# V2P008 TGCARS — development adapter result

**Composition:** LCB `GuaranteeTransportGateV0` + Foundry `P135 CARS`

**Name:** Transport-Gated Certificate-Aware Resolution Sensing

## Neutral primitive

`deletion certificate -> audit transport of its supporting residual/conditional law -> reuse zero-consequence sensing weights only inside transport shell -> otherwise restore non-zero feature sensing weights + require re-certification`

## Honest interface

P135 CARS is valid only inside the TSRC deletion shell and protected action target. Its current implementation can nevertheless be called again in a new deployment environment with no explicit test that the law supporting that guarantee transported. K071 supplies exactly that missing gate: source-standardized residual mean shift + residual scale-ratio shift + optional target residual/driver dependence.

TGCARS preserves exact P135 allocation when the declared transport score is within threshold. When transport is not certified, it does **not** call the deleted feature scientifically irrelevant and does **not** silently continue P135 zeroing. Deleted features regain non-zero declared consequence weights and ACRA is re-solved under the same budget. This fallback is a conservative sensing policy only; it is not a renewed action-invariance certificate. The action guarantee must be re-certified.

## Contrastive boundary benchmark

The deterministic shifted-shell benchmark makes `nuisance` the high-cost feature selected for deletion by TSRC. Blind P135 reuse therefore gives it zero consequence and spends the only fine-resolution slot on `critical`. A pure residual mean shift pushes the K071 transport score above the declared threshold; TGCARS disables zeroing and the same budget now assigns the fine slot to `nuisance`.

Using benchmark-only hidden target consequence weights (not supplied to either algorithm), guarded oracle decision loss is lower than blind reuse. The benchmark establishes the mechanism in this synthetic shell; it is not a deployment-calibration claim.

## Working region

- Same protected action target and P135 feature shell.
- Residual samples are finite and sufficiently supported.
- Source residual scale is identified.
- A transport threshold is declared before target evaluation.
- The ACRA fallback budget/options remain feasible.

## Failure / abstention region

- Too few residuals, non-finite values, unidentified source scale, or malformed target driver: transport is not certified and zeroing fails closed.
- A failed transport audit does not identify which structural assumption changed.
- The fallback's declared feature weights are not themselves a new transport certificate.
- Real deployment requires domain-native calibration and held-out transport checks.

## Development checks

- 12/12 focused tests pass.
- Stable-shell branch matches P135 exactly.
- Mean, variance, and conditional-driver shifts independently disable deletion-certificate zeroing.
- Mechanism-removing comparator is blind P135 certificate reuse.

**Evidence:** executable deterministic-shell mechanism result; not held-out transfer or production readiness.
