# Q196 Dual Defect Derivation (§§12-15, verified by execution)

## §12 dual formulation (derived + checked)

Covector λ with λ∘J = λ (i.e. λ·R_j = λ_j on Jm rows) satisfies
λ((I+J)c) = λ(c) + λ(Jc) = 2λ(c) (char ≠ 2). Hence λ(E) = 0 ⟺ λ(C) = 0,
and the defect dual is L_ξ = {λ : λ∘J = λ, λ(C) = 0}.
Checked: dual J-even space dim = H; invariance λ·R_j = λ_j per basis
vector; dim L = 2 on sampled sectors (d = 5, 7, 3); λ(C) = 0 direct.
(Chronological intervals make C-constraints explicit, no matrix needed.)

## §13 scalar laws (derived + checked)

ℓ_0 = λ(1); z_h = λ(R_h) − ℓ_0/2. Then λ(Γ[a,b]) = Σ_{h=a+1}^{b}
ξ^{P_b−P_h} z_h, so annihilation gives: length-1 [a,a+1]: z_{a+1} = 0;
length-2 [a,a+2]: ξ^{s_{a+1}} z_{a+1} + z_{a+2} = 0. Both verified on
computed λ bases (a driver sign slip s_a→s_{a+1} was caught by this
check and fixed; the spec's formula confirmed).

## §14 boundary parametrization (verified)

Evaluation L → K² at (B, Q) is an isomorphism exactly at det ≠ 0 cells
(checked: dual dets 48, 70 nonzero agree with V1 full-closure cells).
Thus every defect functional is determined by its two boundary values —
the "two boundary parameters", canonically (λ(B), λ(Q)). No source
reflection identities beyond the verified J-geometry were needed or used.

## §15 boundary evaluation (verified)

λ(B) = 2λ(b_in) used throughout (J-evenness); b_in single-interval form
Γ[T_0,T_1] with weight 1; Q^P via P(x) = R_d(x) (P-formula verified for
all tested (d, n_0)). No full H×H matrix evaluated in this route.
