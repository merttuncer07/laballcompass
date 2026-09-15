# Hidden-Mode Resilience Monitor

HMRM turns **IM-306 → IM-222** into an operational monitor. It decomposes a local transition model
into modes, measures the current consequence-bearing exposure of each mode, and estimates how long
that exposure takes to decay below an operational floor. An alarm requires both material exposure
and long recovery.

This distinguishes three cases that a single indicator confuses: visible but fast deviations,
inactive slow modes, and slow modes hidden by cancellation in an observed scalar.

## Run

```powershell
python -m unittest -v test_hmrm.py
python demo_hidden_resilience.py
```

## Product boundary

v0.1 assumes a real diagonalizable local linear transition. Next layers are noisy online fitting,
nonnormal/transient modes, uncertainty intervals, changing baselines, and intervention-aware alarms.
