# Q196 Exact Phase Signs + Three-Layer Forms (§§5-7, 9)

## MU0–MU2 (from PH + PG by exact division)

μ_a = ⌊n_0a/3⌋. With m_a = n_0(a+1), τ_a = [m_a]_3:
μ_{h_a} = dn_0 + (d−1−a) + max(e−a,0) − 2⌊m_a/3⌋ − τ_a;
μ_{q_a} = μ_{h_a} + 1_{a≤e} + ⌊(τ_a+n_0)/3⌋.
(Derivation: μ = (P−ρ)/r with ρ from PG; the floor identities use
2⌊m/3⌋+τ = (2m+τ)/3 and τ'_a = [τ_a+n_0]_3. Machine-checked d ≤ 31.)
Signs ε = (−1)^μ. No fitted tables; residue periods (if any) follow
afterward, never assumed.

## END1–END2 (§6)

S_{r−1} = Σ_{a<d}(x^{−P_a} + x^{−P_{h_a}} + x^{−P_{q_a}}) (partition §3),
reduced by x^r = −1 to Σ_a[ε^{(0)}x^{−ρ^{(0)}} + ε^{(h)}x^{−ρ^{(h)}} +
ε^{(q)}x^{−ρ^{(q)}}] with ρ from PG. R_{r−1} = x^{P_{r−1}}S_{r−1}.
Verified per cell in driver.

## Three-layer algebra + J (§§7, 9)

Y = x^d, Y^3 = −1; ω = ξ^d, ω^3 = 1. S_{r−1} = Σ_a x^{−a}F_a(Y) with
F_a(Y) = ε^{(0)}Y^{−[n_0a]_3} + ε^{(h)}Y^{−[n_0(a+1)]_3} +
ε^{(q)}Y^{−[n_0(a+2)]_3} ∈ span{1,Y,Y^2} (reduce Y^3 = −1).
J in grid coords (x^{a+dt} monomials): JG1 (a > 0):
Jx^{a+dt} = −ξ^{a+dt}x^{(d−a)+d(2−t)} since r−(a+dt) = (d−a)+d(2−t);
JG2: JY^t = −ω^tY^{3−t} (t = 1,2); J1 = 1. All verified per cell.
Dual grid moments M_{a,t} = λ⋆(x^{a+dt}); λ∘J = λ becomes explicit
reflection relations among M_{a,t} (used in transfer search).
