# Q196 H_Q Transfer (§§10-11: exact identities + measurement verdict)

## TR1–TR4 (proved shape, machine-checked d ≤ 11 both n_0, ring identities)

q_a = h_a + 1 with g_{h_a} = r·1_{a≤e} (h_a odd; ≥ 2d−1 ⟺ a ≤ e):
R_{q_a} = 1 + σ_a Y^{n_0} R_{h_a}, σ_a = −1 (a ≤ e) / +1 (a > e). ∎
q_a ∈ B for a ≥ 1 (q_a − (d+1) = 2(d−1−a), even, in range): boost gives
R_{h_{a−1}} = 1 − Y^{n_0} x^{−1} R_{q_a} since s_{q_a} = n + (r−1)
i.e. x^{s} = −x^{n−1} in the ring. ∎ TR3 by substitution; TR4 by
x^{−(a−1)}-framing (H_a = x^{−a}R_{h_a}): H_{a−1} = x^{−a}(x−Y^{n_0}) −
σ_a Y^{2n_0} H_a. Two species (±1). All identities verified as exact
ring equalities (integer coefficient vectors).

## Transfer measurement (§§11b, 13) — negative

Moment chain m_a = (M_{a,t}) shows NO species-constant affine law:
order-1 fit/verify fails (d = 11, 15, both species); order-2 fails
non-vacuously (d = 19, 21, both n_0; fit 7 steps, verify rest).
a-variable C-equations are dense (full support). Primal elimination:
M_E dense 0.95–1.00, full bandwidth, no-pivot fails row 1.
Verdict: no bounded transfer at tested widths; no triangularity.
Per §18: failure reported, nothing invented.
