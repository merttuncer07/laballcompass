# P048 SARA v0.1 — Structural-vs-Approximate Reduction Audit

## Composition
CORMA → BRED. CORMA defines the structural controllable-observable minimum dimension; BRED may reduce below it only by spending approximation error.

## Benchmark result
The 3-state system has CORMA minimal I/O dimension **2** and one structurally redundant state. With BRED error budget **0.1**, selected order is **2** and the reduction is labeled structural redundancy only. With budget **0.5**, BRED selects **order 1** with nonzero error bound **0.47827**; SARA labels this `APPROXIMATE_IO_TRUNCATION_BEYOND_REDUNDANCY`.

Promotion state: **WORKING_COMPOSITION / REDUCTION-CLAIM AUDIT**.
