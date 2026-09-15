# RX-138 — ImplementabilityIroner destructive benchmark r02

Verdict: **SURVIVES**

r01 produced only one median monotonicity reversal, narrowly missing the predeclared nonmonotone-shell
strength gate. r02 increases oscillatory score structure while keeping the monotone control unchanged.

Main shell:
- median raw monotonicity violations: **3**
- ironed violations: **0**
- median fraction of decisions changed: **20.0%**
- median regret vs exact optimal monotone threshold: **0.00e+00**

Monotone control:
- changed fraction: **0.00%**
- regret: **0.00e+00**

Product rule: if raw marginal scores produce an unimplementable nonmonotone allocation, iron/project
them into the feasible monotone class and verify against the exact constrained optimum.
