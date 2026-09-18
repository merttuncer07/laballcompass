# Q196 Phase-Grid Theorem (§§3-4, 8 — proved, machine-checked to d = 31)

Let d = 2e+1, r = 3d, n = dn_0, n_0 ∈ {1,2}.
h_a = r−2−2a, q_a = r−1−2a (0 ≤ a < d).

## Partition

{a} = 0..d−1; {h_a} = odd numbers d..r−2; {q_a} = even numbers
d+1..r−1. Disjoint, union {0,...,r−1}. ∎

## Gap chart (from schedule_L3, both n_0)

g = 1 on [0,d−2]; 0 on {d−1,d}; r−1 on even k ∈ [d+1,3d−3];
r on odd k ∈ [2d−1,3d−3] and on {3d−2,3d−1}; 0 on odd k ∈ [d+1,2d−3].
(Exhaustive count 3d; verified against schedule d ≤ 13.)

## PH1–PH2

P_a = a(n+1): prefix a ≤ d−1 sees only unit gaps. ∎
G_{h_a}: mod r, U contributes d−1 and B-points below h_a contribute
−(d−1−a) (exactly the evens d+1..h_a−1 when nonempty); R-points below
h_a are the odds 2d−1..h_a−1, count max(e−a,0). Hence
P_{h_a} = h_a·n + r[(d−1−a) + max(e−a,0)] + a. ∎
PH2: q_a = h_a+1 and g_{h_a} = r·1_{a≤e} (h_a odd ≥ 2d−1 ⟺ a ≤ e),
so P_{q_a} = P_{h_a} + n + r·1_{a≤e}. ∎

## PG0–PG3 (residues mod r = 3d)

P_a ≡ a + d[n_0a]_3; P_{h_a} ≡ a + d[n_0(a+1)]_3;
P_{q_a} ≡ a + d[n_0(a+2)]_3 (reduce PH1–PH2; −2 ≡ 1 mod 3).
For fixed a, {[n_0a]_3,[n_0(a+1)]_3,[n_0(a+2)]_3} = {0,1,2} since
n_0 ∈ {1,2} is prime to 3. Hence {P_i mod r} = Z_r (PG3), proved for
this canonical schedule only (no universal-necessity claim; the old
universal conjecture stays false).

## Grid path (§8)

Layer 1: (a,[n_0a]_3), a = 0..d−1. Then descending:
(a,[n_0(a+1)]_3), (a,[n_0(a+2)]_3), a = d−1..0. Total 3d pairs;
a collision between layers would need n_0 ≡ 0 mod 3 — false. Hence
every (a,t) ∈ Z_d × Z_3 exactly once. ∎

All formulas hard-checked vs schedule code d = 3..31, both n_0
(driver asserts).
