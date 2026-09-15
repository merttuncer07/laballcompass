# Value-first benchmark batch 9

## RX-011 — ConsequenceWeightedResolution
Equal 30-inspection budget: residual-risk-only expected undetected loss 21.67 vs consequence-weighted
12.33 (-43.1%). Equal-consequence control makes them identical. Strong value, but already covered by
the consequence-coverage family; merge, no new core.

## RX-012 — SelfAveragingCertificate
At n=1200 and cluster size20, naive sqrt(n) 95% interval covers only 54.8%; dependence-certified
interval covers 94.6%. Independent control is 94.6% for both and the certificate does not reject.
Merge into EffectiveDiversityGuardV0.

## RX-019 — InternalClockForecaster
Fails strong baseline. Heterogeneous-clock shell: strong wall-time/history model AUC .9986,
log-loss .0476; explicit internal-clock model AUC .9976, log-loss .0743. Close as distinct product.

## RX-038 — InterfaceWidthOptimizer
Exact DP and generic MILP objectives agree to numerical precision (<4.3e-14). At fixed n=100,
MILP/DP median speedup is ~7.6x for widths2-8, ~19.1x at width8. DP runtime grows ~457x and state
count 4->1024 from width2 to width10. Strong survivor: tractability is controlled by interface width.

## RX-017 — EffectiveTopologyRouter
Current usable topology routes succeed 100% vs 88.8% physical shortest and 90.0% reliability-aware
static. Blocked-path-penalized cost 13.10 -> 3.49. Valid but duplicates existing dynamic-topology
products; merge into DynamicNetworkTwin / ResilientFlowRouter.
