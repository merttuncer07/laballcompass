# Q196 Source Recovery (§1)

## SOURCE / UNIONALLPHA STATEMENTS (verified in files/history)

S1 = AI_NATIVE_MATH_MASTER_HANDOFF_2026-09-08.md; Q193/Q194 = interval-code
source file; DB = stored chat history (read-only copy).

1. Surgery (S1 §14 = Q193 repeat, lines 1583-1609; Q193 file §14):
   old F: f_0 < ... < f_{H-1}; P = (d-1,1) < f_0; f_{H-1} = (0,L-1);
   ordered F*: P, f_0, ..., f_{H-2}.
2. W_* = C + <b_in>, W_F = C + <b_out>, b_in = Γ[P,f_0],
   b_out = Γ[f_{H-2},f_{H-1}]; L=3: b_in = Γ[h_{d-1},q_{d-1}],
   b_out = Γ[h_0,q_0] (Q193 file lines 47-104).
3. Defect (S1 lines 1691-1710; repeated 2193-2208, 2345-2348):
   D_ξ = V_+/(I+J_ξ)C; classes [(I+J)b_in] and [P(u)P(v)]; "constant
   boundary closure, conditional on the bulk lemma"; "Show they form a
   basis"; "without reconstructing the full matrix".
4. Telescoping form (S1 lines 1546-1554): ordered selected-surface
   telescoping gives P(u)P(v) + (I+J_ξ)W_ξ.
5. UnionAlpha stopping point (DB todowrite call 8fdaac4e36641739, 22:13Z):
   "Q196: compute boundary defect span conditionally, test on explicit
   sectors" — status pending. NO executed UnionAlpha Q196 calculation
   exists in the 1003 pre-anchor messages or sibling sessions (searched:
   V_+, (I+J), defect, b_in, 2x2, annihilator, boundary closure/determinant,
   P(u)P(v), M_bdry — all hits are pasted-report text, file reads, R211
   code identifiers, or todo mentions).

Conclusion: NO EXECUTED UNIONALPHA Q196 CALCULATION FOUND; Q196 WAS PENDING.

## NEW RECONSTRUCTION (this pass, not source)

- V_+ (ξ) = ker(J_ξ − I) inside A_r = K[x]/(x^r+1); V_− = ker(J_ξ + I).
- E_ξ = (I+J_ξ)C; B_ξ = (I+J_ξ)b_in; Q^P_ξ(x) = P(x)P(ξ/x) with
  P(x) = R_d(x), cross-checked against P(x) = 1 + x^n Σ_{j<d} x^{j(n+1)}.
- Rank test rank[E;B;Q^P] = H; dual annihilator basis λ_1,λ_2 of E^⊥;
  boundary matrix M_bdry with det ≠ 0 as the basis condition.
- Characteristic-zero lifting via the V4 good-reduction lemma.
- Fixed-width determinant pattern survey (§10); b_out diagnostic (§14);
  telescoping interpretation (§15).
