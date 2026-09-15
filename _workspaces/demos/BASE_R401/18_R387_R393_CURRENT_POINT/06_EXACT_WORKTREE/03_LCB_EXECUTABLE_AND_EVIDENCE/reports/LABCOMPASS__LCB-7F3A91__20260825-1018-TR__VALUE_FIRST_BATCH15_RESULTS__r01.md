# Value-first benchmark batch 15

## RX-150 — GreedyExactnessGate
Exchange/cardinality shell: greedy equals oracle in all 1,000 cases. Nonexchange control: greedy is
suboptimal in 99.4%, median greedy/oracle .793. Strong exactness gate; merge into SharedCapacityAllocator.

## RX-172 — DistributedSharedCapacitySolver
Static problems converge essentially to oracle even with sparse communication, proving the basic
decomposition. Dynamic shock r02 is not robust enough: every-step postshock ratio .949 and 20-step
.810 under the chosen update law. Keep only as a static/distributed shared-capacity component.

## RX-010 — AdmissibleShiftRobustOptimizer
When actual uncertainty lies on the law-preserving direction, structured robustness beats ambient-ball
robustness in 99.4% of cases with median worst-payoff gain .190. If shifts are truly ambient, the
ambient policy wins 99.4%. Promote.

## RX-127 — DependentStreamDeviationGuard
Predictable-variance null: early-window IID variance extrapolation false alarm 28.7%; Freedman-style
certificate .57%. Under positive drift, detection is 99.7% vs 70.4% respectively: the certificate
sacrifices power to restore finite-horizon validity. Constant-variance IID control returns to 5.33%.
Promote.

## RX-133 — GroundTruthFreeRiskTuner
Gaussian SURE is near oracle (.2262 vs .2161 MSE) and beats universal threshold .4840 by 53.3%.
Under gross-error contamination, Gaussian SURE degrades to 1.1379 while universal is .8906.
Promote only with an explicit Gaussian/Stein shell certificate and fallback.
