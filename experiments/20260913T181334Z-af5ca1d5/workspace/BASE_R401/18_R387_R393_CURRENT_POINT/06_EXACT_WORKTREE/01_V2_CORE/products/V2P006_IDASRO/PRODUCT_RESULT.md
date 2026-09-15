# V2P006 IDASRO — development adapter result

Composition: LCB `AdmissibleShiftRobustOptimizerV0` + Foundry `P025 IDRE`.

Status: **WORKING_COMPOSITION / DEVELOPMENT_ADAPTER_EVIDENCE**.

The bridge is intentionally narrow. P025 supplies a scalar identified persistence estimate and standard error. IDASRO does **not** reinterpret that standard error as a generic vector uncertainty radius. The caller must certify a local affine downstream map `mu(a) = mu(a_hat) + s(a-a_hat)` and provide its provenance. Then `|a-a_hat| <= z*SE` maps exactly to the one-dimensional mean uncertainty set with direction `s/||s||` and radius `z*SE*||s||`.

For the quadratic K068 shell `mu'w - .5||w||^2`, the historical numerical optimizer is not imported. The exact solution is derived locally: the component of `mu` orthogonal to the declared shift direction is unchanged, while the parallel coefficient is soft-thresholded by the mean-space radius.

In the frozen deterministic near-boundary shell, P025's nominal action certificate survives but its identification-conservative certificate is revoked. Under a separately declared affine decision sensitivity `[3,0]`, the same identification interval yields mean-space radius `0.1764`, reducing nominal parallel exposure `0.12` to zero and improving the exact directional worst-case quadratic objective. A certified zero-sensitivity control leaves the nominal action unchanged.

This is development adapter evidence only. The affine sensitivity law, its validity radius, persistence uncertainty calibration, and external deployment shell remain scientific/modeling claims outside this product.
