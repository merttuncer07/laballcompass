# Target-Sufficient Reduction Certifier

TSRC turns **IM-124 → IM-256** into a working feature-deletion and target-preservation engine.

For a linear decision score, deleting feature `j` changes the score by at most

`|coefficient_j| × deletion_deviation_bound_j`.

TSRC chooses the feature subset that maximizes removable measurement/computation cost while keeping
the total score-error bound inside the protected distance to the nearest action threshold. It then
returns an action-invariance certificate and can verify actual score/action changes on an evaluation
matrix.

## Run

```powershell
python -m unittest -v test_tsrc.py
python demo_target_reduction.py
```

## Product boundary

v0.1 certifies linear scores over a declared bounded-deviation shell. A margin computed from a finite
evaluation table protects that table, not every possible future input. Next layers are interval-
defined domains, nonlinear Lipschitz/remainder bounds, and multiclass pairwise margins.
