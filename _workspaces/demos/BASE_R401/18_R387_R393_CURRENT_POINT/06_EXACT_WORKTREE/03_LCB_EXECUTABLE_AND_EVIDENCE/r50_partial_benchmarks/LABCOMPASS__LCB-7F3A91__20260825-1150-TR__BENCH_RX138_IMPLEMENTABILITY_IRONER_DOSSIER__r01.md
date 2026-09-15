# RX-138 — ImplementabilityIroner
Verdict: **DOES NOT SURVIVE**

Nonmonotone marginal-score shell:
- median raw monotonicity violations: **1**
- ironed violations: **0**
- median fraction of allocation decisions changed: **13.8%**
- ironed regret vs exact optimal monotone threshold: **0.00e+00**

Monotone-score control:
- median changed fraction: **0.00%**
- ironed regret: **0.00e+00**

Product rule: if the raw marginal score induces an allocation rule that violates implementability/monotonicity, project/iron it into the feasible decision class rather than pretending the unconstrained ranking can be executed.
