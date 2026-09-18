# Q196 Leading-Block Char-0 Certificate (Part B)

Claim: for every tested (d, n0) and every divisor s | 3d, some
exact-order-s reduction has det A ≠ 0 (rank A = H−2), certifying the
order-s sector by the V4 good-reduction lemma.

Method: exhaustive per-(d,n0,s) witness search over both V4 primes
(driver-generated Q196_BLOCKWITNESS.txt, 58 rows: one (p, ξ) each).
No sector lacking a witness (driver exits nonzero otherwise — it did
not). Cyclotomic detA ≠ 0 independently verified for the six suspect
sectors (5,1,5), (3,2,9), (7,2,21), (11,2,33), (15,1,45), (15,2,45).

Corrected verdict: the leading-block lemma SURVIVES every tested
characteristic-zero sector. V2's "PIVOT LEMMA FALSE" is WITHDRAWN as a
characteristic-zero statement — the eight cells are MODULAR BAD
REDUCTIONS (single-swap pivots, full closure, good same-order witnesses
at alternate primes), NOT characteristic-zero counterexamples. Finite
in d: no general theorem claimed.
