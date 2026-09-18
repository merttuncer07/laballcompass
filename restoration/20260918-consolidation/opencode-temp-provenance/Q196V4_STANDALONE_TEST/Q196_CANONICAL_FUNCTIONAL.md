# Q196 Canonical Functional (§§5-7)

## Construction

λ⋆ = unique J-even λ with λ(W_*) = 0 and z_{r−1} = 1, solved as H
conditions on the H-dim J-even dual basis (exact elimination; singular
 ⟹ recorded, not forced). Uniqueness: full-rank system ⟺ z_{r−1} ≠ 0
on the W_*-annihilator line; verified per cell (Q196_LSTARWITNESS.txt,
58 order-sectors). Four modular cells lack λ⋆ (same list as §4
degeneracies); same-order witnesses cover their sectors.

## Verifies (§7)

λ⋆(C) = 0; z_{d+1} = 0 (= λ(b_in), automatic); z_{r−1} = 1;
J-evenness by construction; Θ := λ⋆(Q^P) with Q^P via grouped
double-sum expansion cross-checked against dense polymod route.

## Agreement

Θ ≠ 0 ⟺ rank(E+B+Q^P) = H on all 752 λ⋆-cells. Θ = 0 exactly at the 10
V1 collinear cells. Hence: [B_in],[Q^P] span V_+/E ⟺ Θ ≠ 0 — the §6
equivalence, machine-checked. (Consistency note: Q196 may be called
PROVED CONDITIONAL ON Q195 only with arbitrary-d nonvanishing, which is
not established; general Q195 is OPEN.)
