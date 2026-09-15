# Value-first benchmark batch 3

## RX-040 — HiddenMassLinkage
Moderate linkage ambiguity: hard-MAP population RMSE 4066 versus posterior propagation 302,
a 92.6% reduction. High ambiguity: 97.7% reduction. Clean identifiers collapse the difference.
An overconfident linkage posterior reverses the result and is worse than hard linking.
Product requirement: calibrated match posterior -> overlap distribution -> hidden-mass distribution.

## RX-072 — DynamicNetworkTwin
Expected lost-demand MAE: frozen/no-rewire static 84.73; optimistic static max-flow 78.85;
dynamic topology twin 19.87. This is a 74.8% reduction versus the better static baseline.
With q=0 the dynamic model becomes exactly the static one. Miscalibrating rewiring/overload rules
raises twin MAE to 62.69. Product requirement: graph transitions are state, but transition laws
must be estimated from logs.

## RX-050 — CausalEdgeValidator
Pooled A-B correlation is deliberately matched across direct, confounded and mediated worlds.
Pooled-only classification is 33.3%; valid control+mediator diagnostics reach 100% in the reduced
simulation. Invalid negative controls collapse direct-world accuracy to 26% and falsely label
74% as confounded. Product requirement: return underdetermined unless the causal/design validity
of each control is explicitly defensible.

## RH-009 — ConsequenceWeightedCoverage
Under a fixed audit budget, hard critical-region coverage plus consequence-weighted depth lowers
weighted miss from .4253 to .3083 (-27.5%) versus coverage-only while leaving zero critical regions
uncovered. Pure expected-value allocation is slightly lower loss but leaves a median 3 critical
regions completely uninspected and violates coverage in 97.6% of maps. Equal-consequence control
collapses the distinction. Wrong consequence maps leave median 7 true critical regions uncovered.

## RX-077 — PerimeterMigrationScanner
After risky activity migrates from 80% regulated-category share to 25%, perimeter-only incident
RMSE is 2.193 versus 1.427 for function-equivalent tracking (-34.9%), 12/12 seeds. No-migration
control is nearly equal. If substitute activity is actually only 20% as risky but mapped as 1:1,
functional tracking becomes substantially worse. Product requirement: functional equivalence
weights must be calibrated to downstream outcomes.

## RX-016 not forced into this checkpoint
The current proxy/trigger benchmark changes conclusion depending on whether the deployment
objective is average prediction loss or worst-group/basis-risk control. That utility must be
declared before a scientifically honest product benchmark can be run.
