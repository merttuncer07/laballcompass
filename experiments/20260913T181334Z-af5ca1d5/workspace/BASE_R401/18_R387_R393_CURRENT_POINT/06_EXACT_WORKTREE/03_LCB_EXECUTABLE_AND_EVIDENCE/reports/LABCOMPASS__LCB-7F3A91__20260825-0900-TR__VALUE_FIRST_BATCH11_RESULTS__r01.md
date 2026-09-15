# Value-first benchmark batch 11

## RH-001 — ResidualGuidedClosureFinder
Fails strong matched-budget baseline. With exactly 350 expensive hidden-state measurements,
random resolution RMSE .22583 vs residual-guided .22586. Strong cheap-observable black box .22818.
Residual-guided acquisition provides no material value in the tested localized missing-state shell.

## RH-003 — EvidenceFlowEngine
Mechanism is valid but not distinct enough. Net-balance AUC .495 while cycle/evidence-cycle AUC is
~.9998; however gross-flow baseline is already .99864. Keep circulation as an interpretable
zero-net-flow/audit explanation layer rather than a new detection core.

## RX-014 — SetValuedAbstention
r01 only proved generic selective classification. r02 compares set-integrated and midpoint-confidence
abstention at identical coverage. At 70% coverage both error rates are 3.956%; at 95% the set-aware
version is worse (10.00% vs 9.15%). Close the set-valued-specific product claim.

## RX-059 — ValidationBlindSpotAudit
The existing validator misses 100% of constructed harmful nullspace faults, so the coverage diagnosis
is structurally correct. Under a fair 3-probe noisy budget, random extra checks detect 7.17% and
nullspace-targeted checks 11.33% (+4.16pp), both at ~1% clean FPR. Keep the span/nullspace report as
a diagnostic, not a standalone product.

## RX-073 — BottleneckRegimeMonitor
Fails both extrapolation r01 and online r02. Online median RMSE: static 5.77, rolling local 4.46,
fragmentation gate 5.85. It loses to the strongest baseline by 31.2% and wins only 2/40 seeds.
Close this formulation.
