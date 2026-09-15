# Orthogonal Target Estimator

OTE turns **IM-256 → IM-307** into a working target-estimation engine. It uses a compact
target-relevant representation to estimate treatment and outcome nuisance functions, cross-fits
those predictions, and solves an orthogonal residual score for the protected target.

The first-version score is

`mean[(D-m(X)) × (Y-l(X)-theta(D-m(X)))] = 0`.

At the correct nuisance functions, small nuisance errors have zero first-order effect on the score.
The output includes the target estimate, standard error, 95% interval, and residual-treatment
variation diagnostic.

## Run

```powershell
python -m unittest -v test_ote.py
python demo_orthogonal_target.py
```

## Product boundary

v0.1 uses cross-fitted ridge nuisance models and a partially linear target. It requires residual
treatment variation and does not itself establish causal identification. Next layers are nonlinear
nuisance learners, clustered/time-series splitting, and explicit overlap/support diagnostics.
