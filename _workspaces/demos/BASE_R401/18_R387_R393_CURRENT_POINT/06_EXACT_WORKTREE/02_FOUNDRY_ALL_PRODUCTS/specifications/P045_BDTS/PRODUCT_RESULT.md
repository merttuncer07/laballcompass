# P045 BDTS v0.1 — Breakthrough Distance-to-Tipping Surface

## Composition
PCBE → TDSX. The tipping metric is the minimum of normalized spanning-path bottleneck and normalized system-level conductance jump, so threshold crossing requires both PCBE breakthrough conditions.

## Benchmark result
Baseline channel multiplier **2** gives bottleneck **2.0**, conductance jump **1.3333**, and no breakthrough. The nearest declared one-way flip is channel multiplier **3**, where bottleneck reaches **3.0** and system jump **1.6667**, producing `SPANNING_CHANNEL_BREAKTHROUGH_DETECTED`. A channel that spans at multiplier 3 against background 0.5 but lacks the required system jump remains rejected.

Promotion state: **WORKING_COMPOSITION / BREAKTHROUGH TIPPING BENCHMARK**.
