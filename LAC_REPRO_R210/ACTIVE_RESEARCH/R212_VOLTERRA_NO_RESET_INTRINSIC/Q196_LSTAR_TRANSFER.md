# Q196 λ⋆ Transfer Status (§§13-16, Part O)

## What was attempted

Moment transfer m_{a−1} = T_{σ_a} m_a + f_a (3-state, 2 species) and
order-2 variant, by exact fit-on-subset/verify-on-rest over finite
fields (non-vacuous: more steps than unknowns). Dual z-route and
a-variable density measured in parallel.

## Results (all exact, finite)

- Order-1 affine: NO FIT (d = 11, 15, both species; verified on held-out
  steps; d = 9 and below vacuous/insufficient).
- Order-2 affine: NO FIT non-vacuously (d = 19, 21, both n_0 tested
  where step counts allow: fit 7, verify 1–3, all fail).
- a-variable C-equations: dense full support (measured d = 5, 7, 9).
- Primal M_E: dense 0.95–1.00, full bandwidth, no-pivot fails row 1.
- Positive finite facts retained: (z_{d+1}, z_{r−1}) parametrization
  (preferred + universal fallback), triangular M_Q196 with det 2B_Q,
  B_Q table (V4), Θ agreement.

## Part-O obstruction (exact, minimal)

No species-constant affine transfer exists for the λ⋆ moment chain at
tested widths (3-state order-1/order-2). Smallest unresolved object:
closed (d, ξ)-formulas for the propagation coefficients (A_Q, B_Q) and
the (α,β) change of basis — equivalently a proof that none exists in
bounded width. The dual 2D framework (V4) is verified executable and is
the recommended attack surface; the primal transfer route is closed
by measurement, not by conjecture.
