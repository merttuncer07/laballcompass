# Q196 Provenance V5

## V5 verdicts (all machine-checked this pass)

- Phase-grid theorem (partition, PH1/PH2, PG0-3, MU0-2, grid path):
  PROVED combinatorially from the schedule; asserts pass d ≤ 31
  (partition/PH/PG/MU) and grid-path visit-once to 31.
- TR1–TR4: VERIFIED as exact ring identities d ≤ 11 both n_0
  (x^{n+r} = −x^n and x^{−1} = −x^{r−1} used explicitly; formal-only
  comparison would be wrong — documented).
- END1/J-grid: VERIFIED on sample cells.
- z-system shape + 2z identities: carried from V3/V4 (frozen).
- Transfer: NO bounded transfer (order-1/order-2 fit-tests fail
  non-vacuously; dense widths). Part-O obstruction recorded above.
- Θ closed form: NOT obtained. V4 finite tables stand.
- B0/P (V4 §15): B_0 is a reference-decoder tail row in the stripped
  setting where reflection provably does not descend — cannot be
  inserted into the pre-quotient interval code. Unused, correctly.

## Test-side defects fixed this pass

Import scoping (QV local rebinding), D31 tuple primes, missing r = 81,
87, 93 primes (163/349/373 + Fermat check), unpack mismatch (s/R swap),
formal-vs-ring comparison for TR (sign/negative-exponent handling).

## Status (Part P rules)

- Tested finite cases: CHAR-0 FINITE CERTIFIED (V4; untouched).
- Q196 general: OPEN (conditional structure + obstruction, no proof).
- Q195 general: OPEN. Lemma B, L>=5: untouched.
- No KILLED verdicts. No modular drop promoted.
- All prior packages sealed (mtimes verified at packing).
