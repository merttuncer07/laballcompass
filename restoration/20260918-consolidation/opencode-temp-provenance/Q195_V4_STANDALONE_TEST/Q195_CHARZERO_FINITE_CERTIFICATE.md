# Q195 Characteristic-Zero Finite Certificate (V4 §§5-6, 11)

Machine: q195_charzero_finite_cert.py, clean-room run, exit 0.
Lemma: Q195_GOOD_REDUCTION_LEMMA.md. Per-order coverage verified
operationally (every divisor s|r has a passing exact-order-s cell).

## §5 table (certifying = second prime, ALL r roots pass)

```text
d n0 r  cert-p roots minRankC minJoint target     CHAR-0
3 1 9   37     9     3        6        3/6        CERTIFIED
5 1 15  61     15    6        12       6/12       CERTIFIED
7 1 21  127    21    9        18       9/18       CERTIFIED
9 1 27  163    27    12       24       12/24      CERTIFIED
11 1 33 199    33    15       30       15/30      CERTIFIED
13 1 39 157    39    18       36       18/36      CERTIFIED
15 1 45 271    45    21       42       21/42      CERTIFIED
3 2 9   37     9     3        6        3/6        CERTIFIED
5 2 15  61     15    6        12       6/12       CERTIFIED
7 2 21  127    21    9        18       9/18       CERTIFIED
9 2 27  163    27    12       24       12/24      CERTIFIED
11 2 33 199    33    15       30       15/30      CERTIFIED
13 2 39 157    39    18       36       18/36      CERTIFIED
15 2 45 271    45    21       42       21/42      CERTIFIED
```

Targets rankC = H−2, joint = r−3. One prime covering all roots certifies
every cyclotomic order s|r simultaneously (Galois invariance + lemma).

## §6 formal transversality

dim C̃→ = dim C̃← = H−2 and C̃→ ∩ C̃← = 0 at certifying primes, all roots,
all tested (d, n0). Logically separate from the collision condition.

## §11 three quantities (per certified cell)

A. formal intersection dim = 0.
B. physical collision kernel dim = 0.
C. polynomial intersection dim = 0.
Equivalence B = C holds under the verified generator-rank hypotheses;
A is independent (V3's anomalous cell: A = 0 with modular B = C = 1,
now certified as bad reduction at order 7 by (127, 4)).

## Status

EXACT CHARACTERISTIC-ZERO FINITE CERTIFICATE for the listed (d, n0),
every ξ^r = 1. Finite in d: GENERAL d THEOREM OPEN. Q196 untouched.
