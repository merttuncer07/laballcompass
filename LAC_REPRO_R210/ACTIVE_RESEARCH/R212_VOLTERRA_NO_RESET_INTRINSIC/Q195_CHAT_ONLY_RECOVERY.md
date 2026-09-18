# Q195 Chat-Only Recovery — Master Note (Step 18)

Sufficient for another researcher to understand what UnionAlpha actually
accomplished without reading the original chat. Evidence grade per item:
[SOURCE] (S1/Q193-Q194), [CHAT] (transcript block), [RECOMPUTED] (replay).

## 1. Exact chronology [CHAT Block 8, RECOMPUTED]

T = ordered F* prefix times via ts[('h',a)] = r-2-2a,
ts[('q',a)] = r-1-2a, P = ('h',d-1), F = all h + q(a<=e) minus ('h',0).
Recomputed T in Q195_RECOVERED_SWEEP.txt (d=3: [3,5,6,8], etc.).

## 2. Q193/Q194 conventions [SOURCE]

Q195_CONVENTIONS.md: chronology P,f_0..f_{H-2}; C; b_in = Gamma[P,f_0]
(= Gamma[h_{d-1},q_{d-1}] for L=3); b_out; W_*, W_F; recurrence + S_k;
Q_{k+1}; edges; tildeQ_j; pi with anti-periodic sign; J_xi with
pi J = J pi; C̃→, C̃<-; formal vs physical statements kept distinct;
15.5 helical representation. Gamma edge formula: reconstruction, not source.

## 3. P-labeling bug and correction [CHAT Blocks 7-8]

Old: ts[('q',d-1)] = d duplicated ('h',d-1); first generator = 0 vector;
nullity 2 (artifact). Fix: P = ('h',d-1), no override; T unique;
nullity 0. Regression: test_historical_P_mislabel_bug.

## 4-5. Formal forward/reverse construction; projection [SOURCE+CHAT]

tildeQ_j = sum_{i<j}[i->j]; C fwd = consecutive interior diffs;
C rev = J_xi image (index swap); pi([i->j]) = signed x^{P_j-P_i-1}.

## 6-7. Sweep table; formal transversality [RECOMPUTED]

Q195_RECOVERED_SWEEP.txt: 14/14 cells PASS, nullity 0, formal
intersection 0. Formal joint shapes replayed: (90,4), (240,10),
(462,16), (756,22), (1122,28) for d=3,5,7,9,11 (both n0).

Principal observed condition on every cell:

ker pi_xi ∩ (C̃→ + C̃<-) = {0}.

Recovered chronologies T (never printed in chat; recomputed):
d=3: [3, 5, 6, 8]
d=5: [5, 7, 9, 10, 11, 12, 14]
d=7: [7, 9, 11, 13, 14, 15, 16, 17, 18, 20]
d=9: [9, 11, 13, 15, 17, 18, 19, 20, 21, 22, 23, 24, 26]
d=11: [11, 13, 15, 17, 19, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 32]
d=13: [13, 15, 17, 19, 21, 23, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 38]
d=15: [15, 17, 19, 21, 23, 25, 27, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 44]
(identical for n0=1,2; chronology uses only the h/q time maps).

## 8. Non-vacuousness [RECOMPUTED, matches CHAT Block 10]

Ambient E=(r+1)r; projection rank 8/14/20 for d=3/5/7 (ker_pi dim
82/226/442 — hugely nontrivial); joint-code intersection with ker remains
zero. Occupied-bin census: 45 edges -> 17 bins max 5; 120 -> 29 max 8;
231 -> 41 max 10. Each number measures: total formal edges C(r+1,2);
distinct occupied (rem,sign) slots; largest slot multiplicity.

## 9. Enlarged-code negative control [RECOMPUTED, matches CHAT Block 11]

All-pairwise generators (includes b_in/b_out directions): joint shapes
(9,12), (15,42), (21,90), (27,156) with nullities 6, 30, 72, 132 for
d=3, 5, 7, 9 respectively, both n0=1 and n0=2 (mapping explicit in chat).
Fwd-only ranks 3, 6, 9, 12 (= H-1). Nullity-zero depends on the interior
code, not on the projection routine.

## 10. Diagnostic table numbers [CHAT Blocks 9,10,13]

Formal shapes = (edge-space dim E=(r+1)r, joint cols 2x interior gens).
Edge-to-bin lines = (formal edge count, distinct signed bins, max
multiplicity), d=3,5,7. All reproduced in replay; see sweep file.

## 11-14. Helical derivation; closed walk; histograms [RECOMPUTED]

Q195_WIDTH3_TRANSPORT.md: gap map, generated d=5 labels, 16-prefix closed
walk, unsigned/signed histograms — all exact matches, nothing hard-coded.

## 15. Width-3 c_delta representation [RECONSTRUCTED]

c[delta] = (c0,c1,c2) per horizontal walk-displacement; regroup identity
asserted. Representation only; transfer law open.

## 16. What remains mathematically open

General Q195 theorem; even d; d > 15; s=0 untwisted sector; transfer law;
Gamma edge formula as source mathematics; R_0 convention in source terms.
Boxed status: Q195 general theorem: OPEN.
