# Q196 Chronology Lemma (Part E — proved, machine-checked to d = 31)

Let d = 2e+1, r = 3d, t(h_a) = r−2−2a, t(q_a) = r−1−2a,
F* = {q_1..q_{d−1}} ∪ {h_0..h_e} ∪ {h_{d−1}}.

Claim. Ordered F* times: T_0 = d; T_i = d+2i−1 (1 ≤ i ≤ e);
then every integer 2d−1, ..., 3d−2.

Proof. t(h_{d−1}) = 3d−2−2d+2 = d. t(q_{d−i}) = 3d−1−2d+2i = d−1+2i,
so q_{d−1},...,q_{d−e} = q_{e+1} sit at d+1, d+3, ..., 2d−2. Tail:
t(h_a) = 3d−2−2a gives odd offsets {3d−2,...,2d−1} for a = 0..e;
t(q_a) = 3d−1−2a gives even offsets {3d−4,...,2d} for a = 0..e−1
(q_0 at 3d−1 excluded). Union: every integer 2d−1..3d−2. Ordering:
d < d+1 ≤ ... ≤ 2d−2 < 2d−1 holds; count 1+e+(d−1) = d+e+1 = H. ∎

Consequence (Part F). C-intervals [T_i,T_{i+1}], i ≥ 1: exactly e−1 of
length 2, namely [d+2j−1, d+2j+1] (1 ≤ j ≤ e−1), all others length 1;
total (e−1)+d = 3e = H−2. Machine-verified for every odd d ≤ 31.
