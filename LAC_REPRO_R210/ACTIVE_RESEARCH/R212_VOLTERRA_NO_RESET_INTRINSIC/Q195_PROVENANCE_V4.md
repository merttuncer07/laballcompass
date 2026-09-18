# Q195 Provenance V4

## Terminology correction (§0)

V3's "FORMAL/PHYSICAL DISAGREEMENT" renamed: FORMAL TRANSVERSE /
PHYSICAL MOD-p RANK DROP. V3 files untouched; correction applies to V4.

## What V4 did

- Good-reduction lemma proved (Q195_GOOD_REDUCTION_LEMMA.md).
- Exact orders computed for every surveyed ξ (ord_43(4) = ord_127(4) = 7
  hard-checked; bad cells: orders 7, 15, 11).
- All three bad cells certified as bad reduction via same-order witnesses
  at second primes (Q195_BAD_REDUCTION_TABLE.md).
- All 14 (d, n0) certified in characteristic zero at second primes
  covering all r roots + per-order coverage (Q195_CHARZERO_...).
- Formal transversality certified the same way, kept logically separate.
- Historical five certified at second primes; the 2 bad first-prime cells
  reproduced and classified; (15,9),(25,5),(35,14) remain NOT
  RECONSTRUCTED (older source absent everywhere checked).
- Independent cyclotomic cross-check (§9): self-tested Q(ζ_s) arithmetic
  (s = 3,7,11,15), embed-validated builders, targets 18/14/32 all met.
- Implementation defects fixed en route (test-side sign for x^{−2};
  padd phantom zeros carried from V3; Euclid degree init; pivot
  normalization; s=1 hypothesis edge). Mathematics never tuned: failing
  cells were investigated, never adjusted away.

## Mathematical status

Tested finite cases (d = 3..15, n0 = 1,2, all ξ^r = 1): EXACT
CHARACTERISTIC-ZERO CERTIFIED. General Q195: OPEN. Q196: untouched.
Width-3 regeneration: future work (Phase 13+), not this pass.
