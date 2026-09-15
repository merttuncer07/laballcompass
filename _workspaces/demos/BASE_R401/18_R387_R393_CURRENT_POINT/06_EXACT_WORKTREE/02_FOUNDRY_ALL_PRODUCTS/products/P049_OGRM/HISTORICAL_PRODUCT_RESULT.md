# P049 OGRM v0.1 — Observability-Gated Resilience Monitor

## Composition
CORMA → HMRM. A current resilience alarm is cross-checked against the measurement matrix's gain on the risky eigenmode.

## Benchmark result
For transition eigenvalues **0.95** and **0.4**, the slow first mode has exposure **1.0** and recovery **59 steps**. With measurement `C=[0,1]`, CORMA observability rank is **1** and measurement gain on the risky mode is **0**, so OGRM returns `CONSEQUENCE_BEARING_RESILIENCE_RISK_UNOBSERVABLE`. Replacing C with `[1,1]` makes the same risk observable.

Promotion state: **WORKING_COMPOSITION / MONITORABILITY BENCHMARK**.
