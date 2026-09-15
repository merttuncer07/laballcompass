# Multi-Route Failure-Path Architect

MFPA turns **IM-401 → IM-030** into an explicit architecture search. A low-threshold sacrificial
route can raise resistance enough to activate later crack-deflection, pull-out, or transformation
routes. If an activation threshold lies beyond the resistance already accumulated, the crack outruns
that mechanism and the later capacity contributes nothing.

The optimizer divides a fixed mass budget across mechanisms and replays this activation chain under
multiple non-common-mode degradation scenarios. It maximizes worst-case failure energy, then mean
energy and failure-family diversity, and compares the result with every equal-mass single route.

## Run

```powershell
python -m unittest -v test_mfpa.py
python demo_failure_architecture.py
```

## Product boundary

v0.1 is a transparent surrogate architecture model, not finite-element or specimen validation. The
next shell is calibrated traction/separation laws, geometry/manufacturing constraints, coupled
mechanism interference, uncertainty, and physical coupon data.
