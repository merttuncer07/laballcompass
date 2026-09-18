# Q196 Exact Definitions + Telescoping Note (§15)

## Objects (all exact, finite-field; char-0 via V4 lemma)

- Ambient: A_r = K[x]/(x^r + 1), K = F_p.
- Involution: (J_ξ f)(x) = f(ξ/x); J1 = 1, Jx^h = −ξ^h x^{r−h}.
  Verified J² = I on every basis vector, every surveyed cell.
- V_+(ξ) = ker(J_ξ − I), dim H; V_− = ker(J_ξ + I), dim H−1 (r = 2H−1).
  Verified at every surveyed cell; char-0 by good reduction (rank(J−I)
  certified ⇒ nullity certified).
- C: exact centered-Gamma common core, H−2 generators (V3/V4 object, b_in
  excluded).
- E_ξ = (I+J_ξ)C; B_ξ = (I+J_ξ)b_in with b_in = Γ[P, f_0];
  b_out = Γ[f_{H-1}, q_0] kept separate (§14 diagnostic only).
- P(x) = R_d(x), verified against 1 + x^n Σ_{j<d} x^{j(n+1)} for every
  tested (d, n_0) (integer-identity, all pass).
- Q^P_ξ(x) = P(x)·P(ξ/x) mod (x^r+1); JQ^P = Q^P verified per cell, so
  Q^P ∈ V_+. This is the source's P(u)P(v) as a product-sector row:
  for uv = ξ, evaluation at (u, v) recovers the scalar P(u)P(v), while
  x ↦ P(x)P(ξ/x) is its V_+-valued lift.
- Annihilator: E in V_+-pivot coordinates (pivots of the V_+ basis
  itself), null basis λ_1, λ_2; M_bdry[i][j] = λ_i(class_j); det ≠ 0 is
  the basis condition (basis-independent up to nonzero scale).

## §15 telescoping interpretation (conceptual, labelled as such)

Summed over the ordered F* chain, consecutive exact-Gamma intervals
telescope the quadratic values (Phase-1 identity); the interior
contributions land in (I+J_ξ)C after symmetrization, while the two
exchanged ends survive: P(u)P(v) from the P-head side and the b_in
direction from the surgery. Replacing W_F = C + <b_out> by
W_* = C + <b_in> therefore leaves exactly the recorded 2D defect
V_+/(I+J)C, spanned by [B_ξ] and [Q^P_ξ] wherever det ≠ 0. This explains
the rank pattern (H−2 → H−1 → H) rather than merely tabulating it.
