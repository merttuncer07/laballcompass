# Value-first benchmark batch 22

## RX-155 — DecisionRateDistortion
At a <=5% downstream error target, generic reconstruction-oriented compression fails to reach the
target within tested 1–5 bits (recorded as 6), while decision-distortion compression reaches it at
1 bit. In the aligned control both require 1 bit. Strong extension of DecisionSufficientCompressor,
not a separate core.

## RX-196 — SelectionAwareReferenceLaw
After selecting the largest noisy effect, a naive nominal 95% interval covers the selected true
effect only 40.24% at K=50 and 21.06% at K=100. A selection-aware simultaneous reference law
restores 97.7% and 97.38% coverage. At K=1 both are 95.02%. Promote.

## RX-097 — ObservabilityCoveragePlanner
r01 summary had a pandas column-access bug; stored rows were valid. At the same 8-sensor budget:
random full-rank observability 2.6%, local-SNR 0%, coverage/rank-aware 100%. Median RMSE .6039 ->
.04625. Generic-sensor control gives 100% full rank for every policy. Promote.

## RX-116 — MarkovizationFinder
State+age lowers semi-Markov held-out log-loss .31921 -> .29125 (-8.76%). Geometric-dwell control
shows essentially no difference. Mechanism is valid but misses the predeclared 15% standalone-value
gate; keep as a state-design component.

## RX-163 — ReachAvoidViabilityPlanner
The first grid implementation timed out and was discarded. Analytic r02: endpoint-only direct path
is safe in 0% of obstacle cases; viability detours are safe in 100%, with median extra length .801
and clearance .35. With no obstacle, both policies are safe and detour cost is zero. Promote.
