# Q196 Dual General Derivation (Parts F-M synthesis)

## z-system (Part F)

From the chronology lemma: C gives e−1 length-2 laws
ξ^{s_{d+2j}} z_{d+2j} + z_{d+2j+1} = 0 (1 ≤ j ≤ e−1) and d unit laws
z_h = 0 (2d−1 ≤ h ≤ 3d−2). Count (e−1)+d = H−2. Verified: interval
shapes to d = 31; law values on computed λ bases (V2B).

## b_in anchor (Part G)

b_in = Γ[d,d+1] = R_{d+1} − 1/2 as formal polys (weight 1; verified all
V4 cells). For J-even λ: λ((I+J)b_in) = 2λ(b_in) = 2z_{d+1}. Verified
for both dual-basis vectors at every V4 cell (all ξ, both primes).

## a-expansion verdict (Part J)

In a_0..a_{H−1} variables every C-equation is dense (full support;
measured d = 5,7,9). Dependency width is FULL (H), not bounded. No
chronological transfer in a-space. Reported, not forced.

## Parametrization (Part K, finite-verified)

(α,β) = (z_{d+1}, z_{d+2}) separates L on most cells; observed universal
fallback (α,β) = (z_{d+1}, z_{r−1}) covers the rest (22 cells, all using
z_{r−1}). Structural note: at d = 3, z_{d+2} = 0 identically on L (unit
interval [4,5] ∈ C), forcing the fallback — understood, not anomalous.
Pairwise-exhaustive scan finds a separating pair wherever [B],[Q] are
independent; at the 10 collinear cells no pair separates (correct).

## Anchor + matrix (Parts L-M)

λ(Q^P_ξ) = A_Q α + B_Q β via E^{−1} change of basis (per cell, exact).
Since λ(B) = 2α identically, M_Q196 = [[2,A_Q],[0,B_Q]] is TRIANGULAR
and det M = 2·B_Q. Hence Q196 ⟺ B_Q ≠ 0 (single scalar condition).
B_Q values recorded per cell (Q196_ANCHOR.txt: 378 rows, 4 zeros = the
collinear cells at second primes). det-agreement with canonical Δ holds
on all 378 cells. No closed (d,ξ)-formula for B_Q derived — Part O item.

## Part O obstruction (exact)

Smallest unresolved object: closed ξ-formulas for the propagation
coefficients (A_Q, B_Q) and the (α,β)-change-of-basis as functions of
(d, ξ). Finite evidence + triangular structure + fallback pattern are
preserved above. No interpolation promoted.
