# Physical–Formal Equivalence Lemma (Phase 12)

Conditional exact lemma. No general Q195 proof is attempted here.

## Hypotheses (per surveyed cell, machine-checked where stated)

(H1) dim C̃→ = dim C = H − 2 (formal packets independent; Π-images span C).
(H2) dim C̃← = H − 2 (same for reflected packets onto JC).
(H3) Formal transversality C̃→ ∩ C̃← = 0 (edge level, Π-independent).
(H4) Exact intertwining/projection: Π(JÃ, c) = JΠ(Ã, c); Π(Ã_i, c_i) = Γ_i.

## Lemma

Under (H1)(H2)(H4): dim kerΠ ∩ (C̃→ + C̃←) = dim(C ∩ JC) as coefficient
spaces, hence kerΠ ∩ (C̃→ + C̃←) = {0} ⟺ C ∩ JC = {0}.

Proof: write formal elements by generator coefficients
(α, β) ∈ F^g × F^g, g = H − 2. By (H4) the augmented map is
Ψ(α,β) = Σα_i Γ_i + Σβ_j Γ^J_j with {Γ_i}, {Γ^J_j} spanning C, JC.
By (H1)(H2) both families have rank g. Then
dim kerΨ = 2g − rank(stacked Γ-rows) and
dim(C ∩ JC) = 2g − dim(span of the same stacked rows). Same rows, same
number. ∎

## Why (H3) is listed separately

(H3) does not enter the proof; it is the Q194 bulk input that the physical
test cannot see. The surveyed cell (d,n0,p,ξ) = (7,1,43,4) shows why the
separation matters: there formal transversality HOLDS (intersection 0)
while kerΠ ∩ sum is 1-dimensional AND C ∩ JC is 1-dimensional — the lemma's
equivalence holds (both nonzero), but (H3) alone would have missed the
physical collision. Never merge the two statements.
