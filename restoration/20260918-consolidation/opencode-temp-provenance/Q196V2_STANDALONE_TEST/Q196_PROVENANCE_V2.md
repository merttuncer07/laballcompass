# Q196 Provenance V2

## V1 orientation bug (§1 verdict: CONFIRMED)

V1's Vp (right nullspace of Jm−I) is generally NOT J-fixed (measured:
6/8, 6/8, 10/11 basis vectors fail). Regression test in driver. Root
causes found en route: hand-written Jm had ξ^h for ξ^{(r−h)%r}; row-dot
application for nonsymmetric J; pivot columns of constraint matrix used
for coordinates. All fixed; V1 sealed untouched. V1's ambient ranks/dets
reproduced exactly (same ten bad cells), so its finite verdicts stand.

## Subtlety discovered (recorded, not hidden)

Right-nullspace vectors, wrong as primal basis, are exactly the invariant
dual covectors (λ·R_j = λ_j). A first dual attempt using left-nullspace
vectors failed loudly (det 0 at a good cell); diagnosis pinned the
vector/covector swap. Both orientations now carry machine-checked
J-behavior assertions.

## General-proof status (§§5, 16-18)

- Pivot lemma (§5): FALSE as universal statement (8 full-closure
  counterexamples with single-swap pivots). No leading-block route.
- Transfer (§§10-11): no band/triangular structure (dense, full
  bandwidth). Failed as specified; measurements preserved.
- Dual/z route (§§12-15): VERIFIED executable (dims, laws,
  parametrization). General certificate (§16): NOT claimed — the step
  from finite verification to proof (uniform z-determination across
  all d, reflection closure of z_h) is future work.
- d ≤ 25 inference data: gaps ∈ {1,2} throughout; pivots True + full
  rankEBQ at every sampled cell except the catalogued swaps.

## Status

Q196 finite (d = 3..15, both sectors, all ξ): char-0 CERTIFIED (V1,
re-verified). General Q196: OPEN. First genuine GENERAL-Q196 proof pass
completed with a productive failure on the primal route and a verified
dual framework. L>=5, Lemma B untouched.
