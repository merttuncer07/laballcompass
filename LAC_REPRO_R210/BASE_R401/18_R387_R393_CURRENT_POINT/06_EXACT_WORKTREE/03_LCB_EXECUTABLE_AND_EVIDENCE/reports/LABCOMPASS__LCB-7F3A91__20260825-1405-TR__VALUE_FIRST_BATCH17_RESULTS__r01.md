# Value-first benchmark batch 17

## RX-081 — EffectiveRedundancyAudit
Coherent near-antiphase path pairs make route count almost meaningless. Nominal route-count
prediction median absolute error is 5.956; covariance-aware effective gain is exact to numerical
precision. At K=16, delivered gain is only ~0.72% of nominal route count. Promote.

## RX-160 — ConsumableSafeguardState
r01 had target/state misalignment; r02 evaluated nearly exhausted units only. Corrected heterogeneous
age r03: static protection flag Brier .15898 vs remaining-capacity state .08973 (-43.6%), AUC .913.
Nonconsumable control is identical. Promote.

## RX-175 — InformationSearchTippingGuard
Continuation/hysteresis r02: a 0.0025 acquisition-cost step can drop participation by .861.
Maximum active/inactive equilibrium gap is .9999, with >.30 hysteresis across ~86% of the cost grid.
No-feedback control is smooth and has no hysteresis. Promote.

## RX-180 — ScreeningByDegradationAudit
r01 collapsed to low-type exclusion. r03 forces both types to receive positive quality. Separated
types: IC screening menu yields median +215.3% profit vs optimal pooling and a 2.358 high-low quality
gap. Exact-identical types collapse to zero gain and zero gap. Promote.

## RX-186 — ModeConversionRouter
After a geometry-induced basis rotation, blocked nominal mode A can convert into transmissive B.
A single-channel model has median delivered-power error .668 and misses 88.4% of delivered power.
Conversion-aware model is exact; diagonal/no-conversion control collapses. Promote.
