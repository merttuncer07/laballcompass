# LABCOMPASS LCB-7F3A91 current frontier r26

Date: 2026-08-25 05:32 TR

## Canonical state

- Canonical family frontier: **IM-455**
- Next unused primitive ID: **IM-456**
- Explicit donor provenance: **455/455**
- Curated interaction queue: **211**
- Benchmarked interaction rows: **27**
- Executable top-level prototype cores: **22**
- Old curated `LIVE 5/5` breakthrough frontier remains exhausted.

## New survivor — RX-201 RareWeakLayerMismatchGate

Composition: `IM-311 -> IM-233`.

Narrow claim only: after an upstream structured two-layer/blind-deconvolution fit,
a wrong candidate layer can leave a rare/weak residual trace. An empirically calibrated
higher-criticism test can reject that layer more efficiently than max or energy
**only in the rare/weak shell**.

### r01 calibration failure retained

The first final run used a raw 95th-percentile empirical threshold. The K=8 max statistic
showed **8.25%** false rejection under an independent correct-layer null. r01 was rejected
and remains in the archive as a failed calibration attempt.

### r02 finite-sample empirical-null calibration

Correct-layer null false-rejection rates across K=8 and K=1 tests:
**4.1%–5.8%**.

Rare/weak mismatch:
- energy power: **60.6%**
- max power: **65.5%**
- HC power: **84.3%**

Strong-single mismatch:
- max: **98.6%**
- HC: **98.2%**
- energy: **16.8%**

Dense mismatch:
- energy: **46.0%**
- max: **8.9%**
- HC: **8.8%**

Therefore HC is a shell-specific detector, not a universal replacement.

### symmetry-quotient safety control

Sparse blind deconvolution has scale/time-shift ambiguity.

A one-sample delayed but equivalent kernel is falsely rejected if raw coordinates are
compared before quotienting:
- energy **99.7%**
- max **100%**
- HC **99.5%**

After minimizing over the known support-shift equivalence orbit:
- energy **4.5%**
- max **6.0%**
- HC **4.7%**

A genuine `[1,0.90]` mismatch remains detectable after the same quotient:
- HC **81.3%**
- max **67.3%**
- energy **63.5%**

Hard gates for `RareWeakLayerMismatchGateV0`:
1. held-out/cross-fitted structural residual;
2. independently calibrated correct-layer empirical null;
3. known blind-deconvolution scale/shift symmetry quotient;
4. explicit mismatch-shell selection;
5. max and energy retained as competing controls.

## Novelty status

Higher criticism and sparse blind deconvolution are mature separately.
Targeted prior-art search found no direct higher-criticism post-fit layer-mismatch gate
for blind deconvolution. This is **not** an exhaustive novelty proof.

Provisional scores:
- transfer: **5/5**
- product/commercial: **4/5**

No claim that HC is a new blind-deconvolution solver.

## Binding next line

Continue novelty-aware mining beyond the old curated queue. Apply:
interaction integrity -> existing-core collision -> direct prior art -> destructive
benchmark -> symmetry/invariance controls where the inverse problem has non-identifiability.
Do not mint IM-456 merely because RX-201 survived.
