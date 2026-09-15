# Value-first benchmark batch 16

## RX-065 — GuaranteeTransportGate
Source 90% residual interval is moved through harmless covariate/proxy shifts and harmful
outcome/noise shifts. Marginal covariate-shift score has failure AUC 0.0; invariant residual-law
diagnostic AUC 1.0. Harmless shifts produce 0% material guarantee failures, harmful shifts 100%.
Promote as a distinct deployment-guarantee gate.

## RX-078 — BranchChangeRiskMonitor
Discriminant-distance AUC .776 vs fixed-candidate action-gap .641. Branch-change rate is 34.3% close
to the discriminant vs 5.25% far away. Useful signal, but it misses the predeclared +.15 AUC margin
(observed +.135), so keep as a component rather than a new core.

## RX-104 — RegenerativeRateEstimator
Long-cycle finite-window error .2167 for naive wall-time rate vs .1982 for complete-cycle reward/time
ratio: only 8.5% improvement. Short-cycle control is nearly identical. Keep as a niche estimator,
not a major product.

## RX-139 — LoopyEvidenceGuard
Naive duplicate-message aggregation Brier .0770 vs provenance/effective-independence .05148 (-33.2%);
log-loss .4453 -> .1742. Tree control is identical. Strong result, merged into EffectiveDiversityGuard.

## RX-190 — PostTreatmentConfoundingGuard
True controlled direct effect .94. Within-unit regression adjusting mediator/post-treatment
confounder estimates .302 with median absolute error .638. Sequential g-computation estimates .9403,
error .0110 (-98.3%). Baseline-only confounder control has both errors <.009. Strong result, merged
into TreatmentConfounderFeedbackGuard.
