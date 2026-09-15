# SACPS v0.1 — Support-Aware Covariance and Precision Service

SACPS estimates covariance and precision matrices under a declared dependency support, chooses
diagonal shrinkage by untouched validation likelihood when available, and immediately exposes the
downstream minimum-variance decision.

The output includes exact support compliance, eigenvalue/conditioning diagnostics, portfolio
weights, predicted variance, realized holdout variance, and the realized-risk change versus the raw
sample covariance. Known prior art is not treated as a product veto; the operative question is
whether the estimator produces a stable and measurably better decision on the supplied problem.

Run `python -m unittest -v test_sacps.py` and `python demo_covariance.py`.
