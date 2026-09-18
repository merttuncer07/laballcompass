# Q196 Provenance V3

## What changed vs V2

- Pivot verdict repaired: 8 swap cells are bad reductions (same-order
  good witnesses + cyclotomic detA ≠ 0); "PIVOT LEMMA FALSE" withdrawn
  as a char-0 statement. V2 files sealed; correction lives here.
- Dual route corrected mid-pass: an early version used primal-fixed
  vectors as covectors (caught by det disagreement at a good cell);
  true invariant covectors (right nullspace) verified by the 2z identity
  on all cells. V2B's dual numbers are superseded by V3's (recorded).
- Test-side defects fixed (never the math): x^{−2} sign, padd phantom
  zeros, Euclid degree init, k=0 double count, s-index slip, D31 tuple
  primes, missing r=81/87/93 primes, import scoping, dead code removed.

## Status

- Chronology lemma: PROVED (combinatorial) + verified to 31.
- Phase walk: derived regions + verified d ≤ 11 both n0.
- z-system type: VERIFIED shape; laws verified on computed bases.
- 2z identity: VERIFIED all V4 cells.
- Parametrization/anchor/matrix: EXACT EVIDENCE (finite cells).
- Leading block: CHAR-0 FINITE CERTIFIED per sector.
- Transfer theorem: OPEN (widths full; Part O obstruction recorded).
- General Q196: OPEN. Lemma B, L>=5 untouched. V1–V4, Q196V1/V2 sealed.
