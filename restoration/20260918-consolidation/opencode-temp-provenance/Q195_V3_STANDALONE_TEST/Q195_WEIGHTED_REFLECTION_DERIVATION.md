# Q195 Weighted Reflection Derivation (Phase 4)

Status: DERIVED (not recovered — Phase A proved no explicit formula exists
in stored history). Machine unit tests in run_q195_v3.py.

## Physical involution

(J_ξ f)(x) = f(ξ/x), ξ^r = 1. In the degree-<r anti-periodic basis:
J_ξ 1 = 1; J_ξ x^h = −ξ^h x^{r−h} (1 ≤ h < r), since
(ξ/x)^h = ξ^h x^{−h} = −ξ^h x^{r−h} mod (x^r+1). Verified in code.

## Induced suffix-space involution

Formal packets represent the Q-space before multiplication by x, so the
induced map is Ĵ_ξ = x^{−1} J_ξ x. On monomials:
Ĵ_ξ x^D = ξ^{D+1} x^{−D−2} (x^{−1}·(ξ/x)^D·x = ξ^D x^{−D}, then the outer
x^{−1} and J-conjugation give the stated form; checked term by term).

## Derived edge weight

Edge e = [i→j]: π(e) = x^D, D = P_j−P_i−1. Literal reversal gives
π([j→i]) = x^{P_i−P_j−1} = x^{−D−2}. Hence the weight w with
π(w·[j→i]) = Ĵ_ξπ(e) is w = ξ^{D+1} = ξ^{P_j−P_i}:

J_ξ[i→j] = ξ^{P_j−P_i} [j→i].

Unit tests (machine): πJ_ξ = Ĵ_ξπ edge-by-edge over all formal edges;
J_ξ² = I on every edge (weights ξ^{ΔP}ξ^{−ΔP} = 1, orientation restored).

## J_ξ versus Ĵ_ξ (the Q194 symbol question)

With the derived weight, πJ_ξ = Ĵ_ξπ holds — NOT πJ_ξ = J_ξπ with the
polynomial involution (they differ: on x^h, Ĵ_ξ = ξ·x^{−2}·J_ξ, verified
symbolically: Ĵx^h = −ξ^{h+1}x^{r−h−2} vs Jx^h = −ξ^h x^{r−h}).
Therefore Q194's written intertwining πJ_ξ = J_ξπ must be read with its
right-hand J_ξ as the conjugated suffix-space involution Ĵ_ξ, OR an
additional ξ^{−1}x^2 normalization is missing from the source statement.
Recorded explicitly; not silently identified. The augmented projection
Π_ξ resolves this by construction (Phase 5): Π_ξ(JÃ, c) = J_ξΠ_ξ(Ã, c)
with the POLYNOMIAL J_ξ, verified edge-by-edge in code.

Sharp edge: Ĵ_ξ 1 = ξx^{−2} ≠ 1 (J fixes constants, Ĵ does not), with x^{−2}
the true ring inverse −x^{r−2}. A test encoding x^{−2} as +x^{r−2} fails
exactly at h = 0; the corrected sign is machine-verified on all basis
monomials. This is why the relation is written with true negative powers.

## Answer to the report question

Did Ĵ_ξ resolve the two-power mismatch? Yes: the mismatch is exactly the
ξ·x^{−2} factor above, and the derived weight ξ^{P_j−P_i} absorbs the
ξ-part while the formal packet's x-shift structure carries the rest —
πJ_ξ = Ĵ_ξπ holds exactly, J_ξ² = I holds exactly.
