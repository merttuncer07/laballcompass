# Directional Subcritical-Damage Accumulator

DSDA turns **IM-374 → IM-272** into an early fatigue signal. It accumulates load-weighted,
same-direction log-likelihood evidence from residuals that can each remain below a one-shot alarm
threshold. A hard per-cycle evidence cap and a minimum contributing-cycle count prevent one extreme
observation from masquerading as accumulated fatigue.

Alongside statistical evidence, the monitor carries a nonlinear load-cycle damage proxy. The two
outputs can be compared rather than collapsed into one unexplained score.

## Run

```powershell
python -m unittest -v test_dsda.py
python demo_fatigue_detection.py
```

## Product boundary

v0.1 assumes a known damaging direction and standardized residual. Next layers are learned healthy
baselines, multiple damage directions, variable-amplitude/rainflow cycles, sensor drift separation,
and maintenance-cost calibration.
