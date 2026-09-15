# V2P033 VCMF — Viability-Constrained Multi-Fidelity Budget Controller

A cheap channel can be highly correlated and still be unsafe when its bounded bias can push the inferred state across a viable-set boundary. VCMF enumerates fine/cheap measurement counts under budget, minimizes declared estimator MSE, and adds a CCVC-style hard constraint: worst-case cheap-channel bias must fit inside the current viability margin.

The comparator removes the viability constraint and may choose an apparently efficient but boundary-unsafe mix. Evidence is deterministic bounded-bias mechanism-level only.
