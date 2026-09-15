# RX-149 — SubmodularMarginalAllocator
Verdict: **DOES NOT SURVIVE**

Weighted-coverage allocation, same k=8 budget:
- median gain of marginal-value greedy over top singleton scores: **8.7%**
- greedy wins: **99.9%**
- additive control gain: **0.0%**

Product rule: when item value overlaps, rank by incremental value conditional on the already selected set, not standalone score.
