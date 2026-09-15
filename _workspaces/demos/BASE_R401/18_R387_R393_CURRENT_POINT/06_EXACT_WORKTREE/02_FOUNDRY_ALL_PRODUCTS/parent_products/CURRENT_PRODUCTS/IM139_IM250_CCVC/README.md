# Conservation-Constrained Viability Certifier

CCVC turns **IM-139 → IM-250** into a working certificate and safety filter. It first restricts
motion to the conservation manifold, then asks whether every active safe-set boundary admits a
bounded control whose velocity is tangent or inward. The same constraints can filter an arbitrary
nominal control before it moves the state outside the viable region.

The implementation supports affine continuous-time dynamics, linear conservation equalities,
polyhedral safe sets, bounded controls, vertex enumeration for small systems, local inward-margin
LPs, and a nearest-safe-control filter.

## Run

```powershell
python -m unittest -v test_ccvc.py
python demo_resource_circulation.py
```

## Product boundary

v0.1 handles linear equalities and polytopes. The next shell should support nonlinear learned
conservation surfaces, uncertainty tubes, continuous boundary search, and verified integration
rather than a one-step Euler safety constraint.
