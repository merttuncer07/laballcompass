# P050 CPWT v0.1 — Conservation-Gated Process-Window Tipping

## Composition
CSDC → TDSX. TDSX searches mobility/time process settings, while CSDC supplies both coarsening target attainment and a numerical material-conservation diagnostic.

## Benchmark result
Baseline mobility **0.1**, time **8** reaches mean radius only **1.1149** versus target **1.3**. The declared surface finds a valid target-reaching process point while enforcing maximum relative pre-renormalization volume error ≤ **0.005**. A coarse-step run (`mobility=0.8`, `dt=0.2`) reaches the size target but has volume error **0.01181**, so CPWT rejects it despite nominal target attainment.

Promotion state: **WORKING_COMPOSITION / PROCESS-WINDOW BENCHMARK**.
