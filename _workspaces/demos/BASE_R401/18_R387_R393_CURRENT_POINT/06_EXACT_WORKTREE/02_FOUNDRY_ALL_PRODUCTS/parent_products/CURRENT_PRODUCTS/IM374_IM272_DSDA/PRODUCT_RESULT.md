# Product Result — DSDA v0.1

**Composition:** IM-374 → IM-272  
**Product:** Directional Subcritical-Damage Accumulator  
**Status:** working reference product

DSDA accumulates load-weighted same-direction evidence from individually ordinary residuals. A
hard per-cycle evidence cap and minimum contributing-cycle count prevent one extreme event from
being mistaken for fatigue; a separate nonlinear load-cycle proxy preserves the physical
accumulation view rather than hiding everything in one score.

In 1,600 healthy and 1,600 fatigue episodes:

- DSDA detected **100%** of the constructed fatigue paths before failure, with median lead **297
  cycles**, and produced **0%** healthy false alarms;
- a reachable one-shot threshold detected **80%**, with median lead **330 cycles**, but produced
  **44.31%** healthy false alarms;
- a single arbitrarily large observation cannot trigger DSDA's sequential alarm, while repeated
  subcritical same-direction observations can.

The benchmark is a controlled shell test with a known damaging direction and standardized residual,
not a field reliability claim. Four unit tests pass.

The live extension path is learned healthy baselines, multiple damage directions,
variable-amplitude/rainflow cycles, sensor-drift separation, and maintenance-cost calibration.
