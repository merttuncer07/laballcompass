# Value-first benchmark batch 12

## RX-016 — CalibrationSharpnessProxyGate
Correlation-only proxy selection always picks the highest-correlation but miscalibrated trigger.
Calibration-first/sharpness-second selects the sharp calibrated trigger. Downstream decision cost
falls .2814 -> .2671 (-5.1%). All-calibrated control is identical. Valid component, not a major core.

## RX-082 — DirectionalNetworkState
Same dynamic topology with only edge direction changed. Symmetrizing the transition operator creates
median boundary-load error .0873 and full-distribution L1 error .4608; retaining direction is exact
in the benchmark. Reciprocal control collapses. Strong effect, but merge into DynamicNetworkTwin.

## RX-095 — EndogenousHotspotGuard
After correcting two degenerate shells, r03 has a 28.4% overflow event rate. A constant-retention
model and occupancy-dependent model rank sites similarly (AUC ~.925), but state-dependent retention
cuts Brier .12143 -> .09158 (-24.6%). This is real capacity-risk calibration value. New core.

## RX-124 — ExponentialWorkTailGuard
Rare-weight shell: ordinary relative RMSE .5979 vs pilot-gated exponential-tilt importance sampling
.02455 (-95.9%). Tail sampler activates 100% in the rare shell and 0% in the mild shell, where its
RMSE matches ordinary sampling. Strong survivor; merge into existing RarePathImportanceSampler/deep-tail family.

## RX-146 — ProcessVisibilityCoverageGuard
At fixed 14-region budget, geometric-area selection misses 2.0608 process-mass units vs 1.4270 for
process-measure coverage (-30.8%). Capture of the top 20% process-relevant regions rises 50% -> 100%.
Uniform-process control is identical. Strong survivor; merge into ConsequenceCoverageAllocator.
