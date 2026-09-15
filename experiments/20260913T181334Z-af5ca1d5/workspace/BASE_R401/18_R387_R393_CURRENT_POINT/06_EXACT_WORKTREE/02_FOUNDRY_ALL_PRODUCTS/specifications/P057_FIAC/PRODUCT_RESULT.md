# P057 FIAC v0.1 — Firewalled Information Acquisition Controller

## Composition
MIFF → AICC. MIFF removes suspect-source information-flow paths to the protected controller; AICC then ranks only the channels whose source modules remain reachable after the firewall.

## Benchmark result
Unrestricted AICC prefers `high_info` with expected decision improvement **0.77286**, versus `safe_info` at **0.54922**. The high-information channel originates from the declared suspect module. MIFF cuts `suspect → ctrl`, giving **100% modeled contamination reduction**. FIAC therefore blocks `high_info` and selects `safe_info`.

Boundary: suspect-source and flow semantics are operator-declared; FIAC does not prove a source is malicious and never trades protected-path isolation for information value.

Promotion state: **WORKING_COMPOSITION / INFORMATION-FIREWALL BENCHMARK**.
