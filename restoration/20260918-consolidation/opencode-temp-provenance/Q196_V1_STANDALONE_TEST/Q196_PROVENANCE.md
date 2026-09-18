# Q196 Provenance V1

## §13 verdict

NO EXECUTED UNIONALPHA Q196 CALCULATION FOUND; Q196 WAS PENDING.
Evidence: UnionAlpha todo verbatim ("Q196: compute boundary defect span
conditionally, test on explicit sectors", pending); term searches over
1003 pre-anchor messages + siblings hit only pasted-report text, file
reads, R211 identifiers, and todo mentions. This package is faithful
reconstruction of the pending computation.

## What was built (new, not recovered)

q196_boundary_closure.py + run_q196_boundary.py on frozen V3 machinery
(hash-checked, never modified). V_+ basis/pivots, annihilator dual basis,
2x2 boundary matrix, P-formula cross-check, b_out diagnostic.

## Implementation defects found and fixed (harness only)

- J_matrix hand-written with ξ^h for ξ^{(r−h)%r}: both square to I, so
  only the in-V_+ membership check caught it; matrix now built from the
  verified J_poly (single source of truth) plus a per-cell Jmat==Jpoly
  cross-check.
- Matrix/vector convention: rows-dotted (Jm·v) is wrong for nonsymmetric
  J; corrected to row-combination form.
- Annihilator pivots taken from the constraint matrix instead of the V_+
  basis itself; corrected with basis pivots + assertion.
- Mathematics never tuned: the 10 collinear cells were investigated
  (span ranks + functional values independently agree) and recorded.

## Status

Q196 finite cases (d = 3..15, n0 = 1,2, all ξ^r = 1): EXACT
CHARACTERISTIC-ZERO CERTIFIED (per-order good reduction). Q196 general
theorem: OPEN. Q195 finite: as V4. Q195 general: OPEN. Lemma B, L>=5:
untouched. V1–V4 packages sealed.
