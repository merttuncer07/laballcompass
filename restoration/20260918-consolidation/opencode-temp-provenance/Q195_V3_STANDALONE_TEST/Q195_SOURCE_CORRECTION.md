# Q195 Source Correction (Phase B2)

The V1 recovery faithfully reproduced UnionAlpha's session-2 experiment, but
that experiment's surface object is not the S1/Q193 F*. This file diagnoses
the discrepancy. V1 artifacts are preserved unchanged (HISTORICAL
NEARBY-CODE SWEEP); nothing below edits them.

## B1. Source statements (verified in files)

- F = {(a,2): 0<=a<=d-1} ∪ {(a,1): 0<=a<=e}, L=3 so p=1
  (Q195_CONVENTIONS.md; S1 section 11).
- F* = (F \ {(0,2)}) ∪ {(d-1,1)} (S1 lines 1137-1149).
- Q193: P = (d-1,1), f_{H-1} = (0,2); ordered F*: P, f_0, ..., f_{H-2}.
- L=3: b_in = Γ[h_{d-1}, q_{d-1}], b_out = Γ[h_0, q_0] (Q193 lines 96-104).
- S1 12.1: h_a = R_{r-2-2a}, q_a = R_{r-1-2a}, P = R_d = h_{d-1};
  early tail P, q_{d-1}, ..., q_{e+1} (S1 lines 1235-1267).
- Forced coordinate identification for this correction:
  (a,1) = h_a, (a,2) = q_a. Hence (0,2) = q_0 and (d-1,1) = h_{d-1} = P.
- Therefore F* = {q_1, ..., q_{d-1}} ∪ {h_0, ..., h_e} ∪ {h_{d-1}},
  with P = h_{d-1} and in particular f_0 = q_{d-1}.

## What went wrong (V1 harness)

V1 built (transcript Block 8):

F = [('h',a) for a in range(d)] + [('q',a) for a in range(e+1)],
minus ('h',0), plus ('h',d-1).

Under the forced identification that reads:
{q_0..q_{d-1}} ∪ {h_0..h_e} minus q_0, plus h_{d-1} —
i.e. it swapped the h/q roles of the reference construction AND dropped
the legitimate q_{d-1} = f_0 (for d=3: q_2 never appears; the "fix" deleted
the surface S1 explicitly inserts instead of restoring its natural time).

The correct P fix was: retain q_{d-1} (natural time d+1); add/retain
h_{d-1} = P (time d); remove q_0 = (0,2). Do not replace q_{d-1} by P.

Additionally V1's generator loop began at T_0, thereby including
b_in = Γ[T_0,T_1] and omitting the last genuine common-core interval.
The corrected core is C = span{Γ[T_1,T_2], ..., Γ[T_{H-2},T_{H-1}]} with
b_in, C, b_out kept separate.

## B3. Counts (hard regression)

H = (r+1)/2 = 3e+2 surfaces in F*; dim_generators(C) = H-2 = 3e.
V1 fails this count: d=3 used 2 instead of 3; d=5 used 5 instead of 6; etc.
The corrected harness asserts these counts before any rank test.

## B6/B7 status (from Phase A)

- Gamma[a,b] = tildeQ_b - tildeQ_a: NEW RECONSTRUCTION (no source edge
  formula; no prehistory derivation). Used provisionally, labelled as such.
- Exact J_xi edge weight: NOT RECOVERED anywhere in stored history.
  The corrected harness therefore uses provisional plain reversal ONLY for
  the B9 diagnostic, which must NOT be called Q195.
