# Q196 Boundary Coordinates (§9 + §10 analysis)

## Per-cell data

Q196_FINITE_TABLE.txt: dim V+, rankE, rank(E+B), rank(E+Q), rank(E+B+Q),
defect, inV+, det, b_out diagnostics, for d = 3..15, n0 = 1,2, all ξ^r = 1,
two primes per r.

## Outcome

746/756 cells: defect 2, full span H, det ≠ 0. 10 cells: defect 2 with
[B] ∥ [Q] (both nonzero mod E, collinear) — det naturally uncomputed
(rankEBQ = H−1). Failing ξ (with exact orders): (5,1,31,10:15),
(5,1,61,56:15), (7,1,127,61:21), (9,1,163,150:27), (11,1,67,16:33),
(11,1,67,49:33), (11,1,199,139:11), (3,2,19,11:3), (11,2,67,22:11),
(13,2,79,4:39).

## §10 pattern (reported, not forced)

Zero-dets sit at isolated frequencies, mostly full order r (one order-11
pair, one order-3). No d-mod-6 uniformity: classes {3,9,15}, {5,11},
{7,13} show one zero per (d, p) sector (two at (11,1,67)) with no
cross-prime ξ correspondence and no fixed/formulaic shape detected at
this finite level. det values are λ-basis-dependent (only zero/nonzero
invariant), so deeper cross-ξ comparison would need a canonical
normalization — not attempted (would be new mathematics).

## §14 b_out diagnostic (recorded, not substituted)

746/756 rows: rank(E,B,Q,b_out+) = rank(E,B,Q) — b_out+ adds nothing.
At all 10 collinear cells: rank(E,B,Q,b_out+) = H (full) while
rank(E,B,Q) = H−1, and rank(E,b_out+) = H−1 with b_out+ outside E.
I.e. (I+J)b_out completes the span exactly where (B, Q) fall short.
No substitution claimed; the relation [(I+J)b_out] =? α[B]+β[Q] is false
at those cells (it escapes the B,Q span). Diagnostic only.
