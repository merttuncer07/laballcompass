# Q196 Provenance V4

## B0/P verdict (§15)

B_0 = Q_{0,p−2} is a tail row of the reference-top decoder (S1 §11),
living in the stripped/lower-block setting where reflection famously
does NOT descend (JB_0 = P kills the naive quotient, S1 §13 + Q-surgery
notes). It is not identified with h_0/q_0 anywhere in S1 for L = 3 and
lives in a different (gauged-head) space than our pre-quotient interval
polynomials. Verdict: CANNOT be legally inserted here; unused.

## What V4 established (finite, exact)

- b_out unit form + 2z_{r−1} regression: all cells.
- Boundary pair (z_{d+1}, z_{r−1}): char-0 certified per order (4 modular
  degeneracies witnessed elsewhere).
- λ⋆ exists on 752/756 cells (4 singular = same 4 degeneracies);
  uniqueness by full-rank solve; Θ = λ⋆(Q^P) with grouped anchor.
- Quad telescoping as polynomial identity: all cells, all intervals.
- Propagation + endpoint formulas: verified consequences.
- Θ ≠ 0 ⟺ full span: all λ⋆-cells (10 zeros = V1 collinear set).
- Phase walk explicit; R_{r−1} permutation form; no ξ-narrowing in S1.

## Implementation notes

Driver initially omitted its own __main__ guard and mis-scoped dual
builders (fixed before any logged run; no affected outputs shipped).
V2B dual erratum carried forward (documented in V3 provenance).

## Status (Part P rules)

- Tested finite cases: CHAR-0 FINITE CERTIFIED (Q196 closure).
- General Q196: OPEN (needs arbitrary-d Θ ≠ 0; Q195 hypothesis open).
- Q195 general: OPEN. Lemma B, L>=5: untouched.
- No KILLED verdicts; no modular drop promoted to char-0 fact.
- V1–V4, Q196V1–V3 sealed (this package adds, never edits).
