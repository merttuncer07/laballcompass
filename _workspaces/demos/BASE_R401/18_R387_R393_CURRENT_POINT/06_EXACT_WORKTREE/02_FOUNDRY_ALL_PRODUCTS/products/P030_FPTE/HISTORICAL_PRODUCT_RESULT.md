# P030 FPTE v0.1 — Failure-Path Tipping Explorer

## Composition

MFPA baseline multi-route architecture design -> TDSX frozen-architecture retention tipping surface.

FPTE first optimizes the physical allocation under baseline mechanism retentions. It then freezes that allocation and asks how much declared mechanism/scenario retention can deteriorate before worst-case failure energy crosses the requirement. Stress points are never silently re-optimized.

## Benchmark

Synthetic four-route sequential failure architecture:

- baseline optimized worst-case energy: `4.2863488291`
- required minimum: `4.0`
- nearest wet sacrificial retention tipping: `0.35 → 0.30`
- tipping worst-case energy: `1.6654915228`
- relative energy collapse: about `61.14%`
- at the tipping point the wet scenario activates only `sacrificial_layer`; crack deflection, fiber pullout and phase transformation are no longer reached

The small retention change therefore exposes an activation-bridge cliff that baseline worst-case energy alone does not show.

## Claim boundary

Synthetic mechanism benchmark. Retentions, activation thresholds, mass discretization and dissipation laws require physical calibration before engineering use. The surface measures robustness of the built/frozen architecture, not redesign flexibility.
