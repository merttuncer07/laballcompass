# Product Result — HMRM v0.1

**Composition:** IM-306 → IM-222  
**Product:** Hidden-Mode Resilience Monitor  
**Status:** working reference product

HMRM refuses to infer resilience from one observed scalar or from the mere existence of a slow
mode. It decomposes local dynamics, measures current consequence-bearing modal exposure, estimates
the time for each exposure to fall below an operational floor, and alarms only when exposure and
recovery horizon are jointly material.

In a reproducible controlled benchmark of 1,800 local systems:

- scalar cancellation hid **588 of 600** deliberately loaded slow-mode cases below a 0.02 observed
  distance;
- the scalar-only alarm had **0%** true-positive rate and **19.58%** false-positive rate;
- a recovery-time-only alarm had **93.5%** true-positive rate but **45.67%** false-positive rate,
  because it alarmed on slow modes that were barely excited;
- the joint exposure/recovery rule separated all constructed cases, with **100%** true-positive and
  **0%** false-positive rates in this benchmark.

The last result is deliberately reported as a construction result, not an out-of-sample universal
claim. Three tests pass, including recovery of a known transition matrix from a trajectory.

v0.1 assumes real diagonalizable local linear dynamics. The live extension path is noisy online
fitting, nonnormal transient amplification, uncertainty intervals, baseline change, and evaluation
on actual intervention streams.
