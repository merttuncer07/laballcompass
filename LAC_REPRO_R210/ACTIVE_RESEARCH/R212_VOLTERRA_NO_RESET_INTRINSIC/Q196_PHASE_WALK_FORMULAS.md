# Q196 Phase-Walk Formulas (Part I — derived regions, verified d = 3..11)

Schedule (both n0; g independent of n0): U = [0,d−2] → 1; {d−1,d} → 0;
[d+1,2d−3] → r−1 on evens else 0; {2d−2} → r−1; [2d−1,3d−3] → r on odds,
r−1 on evens; {3d−2,3d−1} → r. Verified against schedule_L3 d ≤ 13.

With Ev/Od = even/odd counts on intervals, G_k = Σ_{j<k} g_j in closed
form per k-zone (code: G_closed), P_k = kn + G_k, P_k mod r and
⌊P_k/r⌋ mod 2 verified against the schedule for d = 3,5,7,9,11 and
n_0 = 1,2 (value, residue, and quotient parity all exact).

Use: R_k = Σ_{i≤k} x^{P_k−P_i} (formal; asserted in driver), hence
λ(R_k) = Σ_{i≤k} (−1)^{q_{k,i}} a_{ρ_{k,i}} with P_k−P_i = q r + ρ, and
a_ρ folded by a_ρ = −ξ^ρ a_{r−ρ} into a_0..a_{H−1}. No hidden matrices.
