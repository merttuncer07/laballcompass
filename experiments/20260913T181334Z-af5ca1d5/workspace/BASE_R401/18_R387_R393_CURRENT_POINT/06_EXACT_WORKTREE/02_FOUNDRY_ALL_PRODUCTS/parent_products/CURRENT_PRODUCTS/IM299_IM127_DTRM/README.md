# Decision Transient Risk Monitor

DTRM is a working tool built from **IM-299 → IM-127**. It answers a concrete operational question:

> Can a bounded uncertainty today be temporarily amplified in a direction that changes which
> action is preferred, even when the system eventually settles?

For a common linearized flow it computes

`TAFI = uncertainty_radius × max_t ||contrastᵀ exp(A t) W||₂ / nominal_action_gap`.

- `TAFI < 1` gives a lower-gap certificate inside the declared linear shell.
- `TAFI > 1` returns the peak time and a concrete admissible initial perturbation capable of crossing
  the action boundary.
- If actions change the system dynamics, DTRM compares the two action-specific propagators instead
  of incorrectly forcing both through one flow.

v0.2 also supports the IM-317 finite-horizon envelope. When only a local inequality
`d||error||/dt <= L||error|| + disturbance` is available, DTRM converts it into a decision-gap bound
without pretending the full trajectory is known.

## Run

Use the bundled environment containing NumPy and SciPy:

```powershell
python -m unittest -v test_dtrm.py
python dtrm_cli.py --input example_common_flow.json
python dtrm_cli.py --input example_action_branches.json
```

## Current product boundary

The v0.2 monitor handles finite-dimensional continuous-time linear systems, ellipsoidal initial
uncertainty. It is directly usable on a supplied linearization. It does not yet certify nonlinear
remainder terms, repeated process disturbances, state constraints, or uncertain action gaps. Those
become explicit construction layers rather than reasons to discard the core operator.
