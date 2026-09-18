# Q196 Explicit Phase Walk (§12, written formulas — no code references)

Gap chart (both n_0; r = 3d): g = 1 on [0, d−2]; 0 on {d−1, d};
r−1 on even k ∈ [d+1, 3d−3]; r on odd k ∈ [2d−1, 3d−3] and on
{3d−2, 3d−1}; 0 on odd k ∈ [d+1, 2d−3]. (Exhaustive: counts sum to 3d.)

Gap sums G_k = Σ_{j<k} g_j, with Ev/Od = even/odd counts on intervals:
- k ≤ d−1: G_k = k.
- k ≤ d+1: G_k = d−1.
- k ≤ 2d−1: G_k = (d−1) + (r−1)·Ev(d+1, k−1).
- k ≤ 3d−2: previous plus (r−1)·Ev(2d−1, k−1) + r·Od(2d−1, k−1).
- k ≤ 3d: G_{3d−2} + r·(k−3d+2).

P_k = kn + G_k (n = dn_0); residue P_k mod r and quotient parity
⌊P_k/r⌋ mod 2 follow by division. Verified (value, residue, parity)
for d = 3,5,7,9,11 and n_0 = 1,2 against the schedule.
