# Value-first benchmark batch 1

## RX-033 — systemic liquidity load sharing
Mechanism direction is consistent in 12/12 seeds. Main shell (`rho=.55`) moves mean defaults
15.35 -> 17.22, p95 39 -> 46, and P(defaults>=20) by +4.58 percentage points. It failed the
predeclared >=10-default +5pp high-impact gate (+2.81pp), so it is retained as a calibrated
systemic-risk component rather than promoted as a breakthrough.

## RX-037 — PipelineRiskState
r01: fails to add value when visible output already leaks damage (baseline AUC ~.98).
r02: in the actual hidden-pipeline shell, current regime/output/age are matched while historical
load burden differs. AUC .5581 -> .8838; log-loss .6853 -> .4361; 8/8 seed wins. Memoryless
control gives no gain. Promote as a shell-gated predictive-maintenance core.

## RX-013 — linkage uncertainty propagation
Moderate ambiguity: RMSE improves 17.55%; high ambiguity: 20.68%; clean-ID control collapses.
However MAE worsens because posterior averaging sacrifices exact zero-error MAP cases to reduce
large linkage mistakes. Promote only as a downstream-loss-aware component.

## RX-042 — rare-event path-informed sampling
At z=4.95, crude Monte Carlo returns zero in 98.33% of 30k-sample replications. Path-informed
importance sampling reduces RMSE by ~828x at equal sample budget. At z=2.83 gain is ~9.94x.
When z<2, rarity gate turns the tilt off. Promote as a high-value simulation core.
