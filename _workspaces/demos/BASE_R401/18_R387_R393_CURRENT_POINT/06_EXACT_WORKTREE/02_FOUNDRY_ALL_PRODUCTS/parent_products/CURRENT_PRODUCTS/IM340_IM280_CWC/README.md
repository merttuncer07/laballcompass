# Calibration Width Controller

CWC turns **IM-340 → IM-280** into a sequential interval-width controller. It separates coverage
error from sharpness and miss magnitude, then feeds only the coverage component into a bounded PI
controller in log-width space. Width and total interval score remain outputs used to judge the
result, not conflated feedback signals.

The included comparator follows the valid stochastic gradient of the full instantaneous interval
score. The benchmark changes outcome variance twice while leaving the supplied base scale stale.

## Run

```powershell
python -m unittest -v test_cwc.py
python demo_coverage_control.py
```

## Product boundary

v0.1 controls symmetric scalar intervals. Next layers are asymmetric tails, conditional/group
coverage, delayed labels, anti-windup under prolonged shifts, and action-cost-aware coverage targets.
