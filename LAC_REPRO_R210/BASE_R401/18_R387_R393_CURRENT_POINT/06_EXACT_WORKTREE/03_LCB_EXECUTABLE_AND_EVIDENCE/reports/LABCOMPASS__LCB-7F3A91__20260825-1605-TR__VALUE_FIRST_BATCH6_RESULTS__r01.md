# Value-first benchmark batch 6

## RX-046 — TargetPopulationAnchor
r02 uses portfolio expected-loss reserve error rather than AUC. With a 30% -> 80% target composition
shift, the 200,000-source model under-reserves by ~10.17%. A target anchor of only 400 labeled cases
reduces error to ~0.84%, ~91.8% reduction. No-shift source model is already essentially calibrated.
Promote.

## RX-052 — AtomicComplementarySettlement
Normal high-success/reversible shell has small benefit; stress shell materially increases atomicity
value. Substitutable legs lose ~7% under atomic coupling. Keep as stress-gated component, not major core.

## RH-007 — MultiFidelityMeasurementController
At rho=.95, same-cost adaptive multi-fidelity RMSE is 47.2% lower than fine-only and only 1.02x
oracle static. At rho=.80 gain is 20.1%. At rho=.10 controller uses multi-fidelity only 8.7% and
stays within ~1.1% of fine-only. Promote.

## RX-031 — BarrierAwareTransitionPlanner
Heterogeneous-barrier graphs: shortest-hop success within horizon .832, greedy-utility .321,
barrier-aware .999. Expected transition time 24.25 -> 9.17. Equal-barrier control collapses to
shortest-hop. Promote.

## RX-036 — ResilientFlowRouter
At 10% edge blockage, frozen surviving throughput median 47 vs rerouted 69 from baseline 73.
Rerouting recovers ~90.8% of otherwise-lost capacity and equals the max-flow throughput oracle.
Zero-blockage control is identical. Promote.
