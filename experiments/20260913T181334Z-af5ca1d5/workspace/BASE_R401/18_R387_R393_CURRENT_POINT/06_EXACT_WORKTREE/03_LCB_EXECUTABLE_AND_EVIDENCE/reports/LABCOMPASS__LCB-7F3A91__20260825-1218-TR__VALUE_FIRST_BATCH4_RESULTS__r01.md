# Value-first benchmark batch 4

## RH-005 — LiquidityStateEngine
r01 failed an arbitrary +.12 AUC promotion threshold despite log-loss falling ~0.295 -> .093.
r02 evaluates the actual funding decision at ~95% shortfall recall: nominal false-positive rate
29.5% vs state-vector 2.4%; decision loss/case 1.232 -> .164 (-86.7%). Under run-stress shift,
1.143 -> .165. All-cash-equivalent control collapses the distinction. Promote.

## RX-021 — CompetingExitExposure
An independent-exit approximation is calibrated to exactly the same unconditional exit hazards
as the true contract. With counterparty-state-dependent exercise it still understates cumulative
positive exposure by 24.7% mean and 19.0% p95. Exogenous-exit control error is near zero. Promote.

## RX-043 — QueryPreservingNetworkCompression
Gomory-Hu trees compress ~200-214 edge graphs to 69 edges, preserve every tested min-cut exactly,
and answer repeated cut queries about 85x faster after build. Median amortization break-even is
~24 queries. Misuse for shortest-path queries gives ~42% median relative error. Promote only for
declared cut/bottleneck queries.

## RX-048 — AdaptiveRegimeMemory
Fails strong baseline. Oracle-tuned fixed window MSE .6247 versus adaptive multiscale .6728.
Stationary control correctly expands to 256-sample memory, but no regime-shell product advantage
was demonstrated. Close pending a materially better detector.

## RH-008 — TriggerQualityEngine
Quality-aware allocation of a 10% verification budget reduces decision cost .1995 -> .1859
(-6.8%) against a strong decision-boundary verification baseline and ~20.5% versus random verification.
This misses the predeclared 8% high-impact gate. Keep as a validated component, not a new major core.
Perfect-trigger control shows verification has no value when basis risk is absent.
