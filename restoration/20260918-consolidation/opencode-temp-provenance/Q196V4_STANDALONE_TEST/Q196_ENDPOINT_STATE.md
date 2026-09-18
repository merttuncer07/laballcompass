# Q196 Endpoint State (§13)

R_{r−1}(x) = x^{P_{r−1}} Σ_{ρ=0}^{r−1} ε_ρ x^{−ρ} with ε_ρ = (−1)^{q}
from P_i = qr + ρ. Verified: {P_i mod r : 0 ≤ i < r} is a permutation
of 0..r−1 for every d ≤ 31, both n_0 (so each ρ occurs exactly once).

Sign species (odd-quotient count by d): n_0 = 1 shows period-12 steps
(+4,+8,+8 per d+2 in the d≡1 mod-4 class); n_0 = 2 shows period-12
blocks (+3,+5,+1,+1,+3,+3). Tables in provenance. This is the finite-
state signal for §17: residue-class dependence is real at the level of
the walk, unfixed in form. Recorded as inference-grade data, not proof.
