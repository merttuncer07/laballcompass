# Value-first benchmark batch 7

## RX-041 — TreatmentConfounderFeedbackGuard
True always-treat vs never-treat effect 2.92. Ordinary regression adjusting for treatment-affected
L1 has median absolute error .723; IPTW .020; g-formula .013. When prior treatment no longer changes
L1, ordinary adjustment returns to .017 error. Promote.

## RX-049 — HiddenStateModelReductionAudit
Corrected r02 fixes an invalid negative control. Persistent hidden-state shell: static reduced RMSE
.7126 vs memory-augmented .5791 (-18.7%) and residual ACF .0968 -> .0253. Truly memoryless control
.5117 vs .5118. Survives as extension of existing MemoryKernelClosureV0; no new core.

## RX-060 — TargetRelevantSensorPlanner
Target-aware C-optimal RMSE 0.2923 vs best strong target-agnostic design 0.3357,
a 12.9% gain. Useful but below the original 20% major-product gate. Keep as component.

## RX-068 — DecisionFlipMargin
Hidden-bias margin AUC .785; conventional z-fragility .796. The proposed ranking does not beat the
strong baseline. Close as standalone product; minimum-bias-to-flip remains useful explanatory metadata.

## RX-084 — BurstAwareSampler
At matched 5% expensive-measurement budget, consequence-weighted burst capture rises from about
4.99% to 14.04% (+181.1%). Homogeneous-burst control collapses
the advantage. Inverted/stale precursor performs 27.5% worse than uniform.
Promote with prospective precursor-calibration monitor and fallback.
