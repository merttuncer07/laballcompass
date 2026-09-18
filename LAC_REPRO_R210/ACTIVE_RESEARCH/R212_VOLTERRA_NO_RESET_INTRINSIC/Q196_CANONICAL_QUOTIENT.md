# Q196 Canonical Quotient (§§3-9)

## §3 canonical even basis (verified per cell)

r = 2H−1; e_0 = 1; e_h = x^h − ξ^h x^{r−h} (1 ≤ h ≤ H−1).
J(e_h) = e_h checked on every basis vector, every surveyed cell
(J(x^h) = (ξ/x)^h = ξ^h x^{−h} = −ξ^h x^{r−h}; constant term fixed).
Rank H checked → basis of V_+. Reconstruction f = Σ_{k<H} f_k e_k
checked for every V_+ basis vector and every E/B/QP vector (uses
J-evenness f_{r−h} = −ξ^h f_h). Only canonical coordinates used downstream.

## §4 M_E + pivot pattern (measured)

M_E(ξ) ∈ K^{(H−2)×H}: E rows in canonical coords. Pivot columns are
{0,...,H−3} on all surveyed cells EXCEPT 8, where exactly one swap
occurs (observed: [0,1,2,3,4,6] d=5 ×2; [0,1,3] d=3 n0=2;
[0..7,9] d=7 n0=2; [0..13,15] d=11 n0=2; [0..19,21] d=15 ×2):
(5,1,31,8:5), (5,1,61,58:5), (3,2,19,6:9), (7,2,43,25:21),
(11,2,67,4:33), (15,1,271,64:45), (15,2,181,9:45), (15,2,271,8:45)
(d,n0,p,xi:order). ALL 8 have full closure (rankEBQ = H).
Verdict: the §5 candidate lemma (universal leading-block invertibility)
is FALSE as stated — counterexample (5,1,31,8). No generalization is
built on it (§18 failure report).

## §§5-6 quotient map (established where pivots hold)

M_E = [A|U], A (H−2)² invertible ⟺ pivot pattern; ρ(v) = v_R − v_L A^{−1}U;
ρ(E) = 0 checked per cell; ker ρ = E by dimension count. Hence
ρ: V_+/E → K². (At the 8 swap cells ρ is not constructed; their closure
is witnessed by V1 ranks/dets instead.)

## §§7-8 residuals and agreement

β = ρ(B), q = ρ(Q); Δ = det(β,q). Verified on all 756 cells:
Δ ≠ 0 ⟺ rank(E+B+Q) = H. Zeros = exactly the V1 ten bad cells.
Canonical normalization (ordered even basis fixed) replaces V1's
annihilator-basis determinant; values differ, zero-pattern identical.
