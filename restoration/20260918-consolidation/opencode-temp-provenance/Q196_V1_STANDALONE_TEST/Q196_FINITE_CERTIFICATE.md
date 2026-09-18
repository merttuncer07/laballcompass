# Q196 Finite Certificate (§12)

Method: V4 good-reduction lemma, per cyclotomic order s|r. A sector is
covered by one passing exact-order-s cell (defect 2, full span H,
det ≠ 0). Driver exit 0 = every divisor order covered for every (d, n0).

```text
(d, n0): per-order coverage COMPLETE (all s | r have witnesses)
(3,1) (5,1) (7,1) (9,1) (11,1) (13,1) (15,1)
(3,2) (5,2) (7,2) (9,2) (11,2) (13,2) (15,2)
```

Isolated modular zeros (10 cells, all orders represented elsewhere by
passing witnesses): listed in Q196_BOUNDARY_COORDINATES.md with exact
orders. Each is a bad finite-field reduction of the determinant, not a
characteristic-zero fact — certified by same-order passing cells.

A/B/C per certified sector: A (formal, from V4) = 0; B (kerPi) = 0;
C (polynomial) = 0. (V4 certifies A and the Q195 input rankE = H−2 that
makes E well-formed; this pass verifies B/Q-span directly.)

Result: Q196 EXACT CHARACTERISTIC-ZERO FINITE CERTIFICATE for the tested
(d, n0), every ξ^r = 1. Finite in d: general Q196 theorem OPEN.
