# P047 RALA v0.1 — Resilience-Aware Lumpability Audit

## Composition
SALC → HMRM. SALC certifies block-transition lumpability; HMRM checks whether consequence-bearing slow modes survive inside a block and are invisible to the aggregate state.

## Benchmark result
A 4-state chain is **exactly lumpable** into two blocks with zero one-step block error. Nevertheless the within-block difference mode has eigenvalue magnitude **0.94**, current consequence exposure **2.0**, and recovery **60 steps**. Its block-sum is zero, so the aggregate sees no current deviation. RALA therefore returns `EXACTLY_LUMPABLE_BUT_RESILIENCE_UNSAFE`. A fast-mixing version of the same partition passes the resilience guard.

Promotion state: **WORKING_COMPOSITION / HIDDEN-MODE AGGREGATION BENCHMARK**.
