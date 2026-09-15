# P038 LIDA v0.1 — Lock-In Damage Accumulator

## Capability

LIDA composes SLERM's windowed synchronization/energy-transfer monitor with DSDA's capped sequential damage evidence. It detects persistent subcritical lock-in that never crosses the one-window dangerous-response threshold but repeatedly transfers positive mechanical work.

## Benchmark result

A phase-locked sinusoidal force/displacement stream produces normalized force-to-velocity energy transfer near 1 in almost every window. Response RMS remains below SLERM's declared dangerous threshold, so **no SLERM window is dangerous**. After standardization against the declared baseline, however, the small same-direction response elevation accumulates through DSDA and eventually triggers a persistent-damage alarm. No individual DSDA residual reaches its one-shot threshold.

A quadrature control with near-zero mean power does not accumulate the alarm, and a short episode is blocked by DSDA's minimum-contributing-cycle requirement.

## Claim boundary

The RMS baseline/scale and endurance normalized-energy-transfer level are explicit operator inputs. Frequency locking by itself is not treated as damage; only positive work transfer contributes load severity, and DSDA retains its influence caps and persistence requirement.

## Verification

5/5 product tests pass.
