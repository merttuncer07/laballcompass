# RX-138 — ImplementabilityIroner destructive benchmark r02

Verdict: **SURVIVES**

r01 produced only one median raw monotonicity violation, narrowly missing the predeclared shell.
r02 uses a more clearly fragmented nonmonotone score.

Main shell:
- median raw monotonicity violations: **3**
- ironed violations: **0**
- median allocation decisions changed: **17.0%**
- ironed regret vs exact optimal monotone threshold: **0.00e+00**
- simple first-positive-crossing repair regret: **0.0346**

Monotone control:
- median changed fraction: **0.00%**

Product rule: when a raw score induces an unimplementable allocation, project/iron it into the
feasible monotone class rather than applying a local repair or executing the raw ranking.
