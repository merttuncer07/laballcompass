# DFDPE v0.1 — Differentiation-Free Dynamic Parameter Estimator

DFDPE estimates the continuous-time affine dynamic system
`dy/dt = persistence*y + input_gain*u + drift` from noisy observations without differentiating the
observed series. Smooth overlapping windows move the derivative from the data onto a known
modulation function through integration by parts.

The product reports parameter uncertainty, window-level residuals and robust weights, excitation
rank, conditioning, and untouched rollout error. A numerical-derivative fit is retained only as an
audit comparison. Underexcited data returns an explicit non-identifiability result instead of a
confident-looking parameter vector.

This is a deliberately usable narrow shell for dynamic cash-flow, inventory, reserve, and risk
systems. Historical prior-art collision remains provenance; it is not a veto on construction.

Run `python -m unittest -v test_dfdpe.py` and `python demo_dynamic_estimation.py`.
