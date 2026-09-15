# P059 SBTE v0.1 — Safeguard Budget Tipping Explorer

## Composition
CSID → TDSX. At each budget, CSID chooses its economically preferred safeguard portfolio. TDSX finds the nearest budget where the selected portfolio reaches a declared residual-loss target.

## Benchmark result
Baseline residual loss is **50** and target is **15**. If two same-family document safeguards are incorrectly treated as independent, the target appears reachable at budget **10**. Family-aware CSID recognizes the common evidence family and requires budget **13** with an independent audit. The optimistic calculation understates required budget by **30%**.

Promotion state: **WORKING_COMPOSITION / SAFEGUARD-BUDGET BENCHMARK**.
