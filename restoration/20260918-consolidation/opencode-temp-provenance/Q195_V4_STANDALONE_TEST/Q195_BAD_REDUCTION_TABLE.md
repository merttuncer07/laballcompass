# Bad-Reduction Table (V4 §4)

Terminology (§0 correction): these are FORMAL TRANSVERSE / PHYSICAL MOD-p
RANK DROPS, not disagreements. Formal transversality holds at every cell
below; the projection rank drops mod p.

```text
object              | d/(r,n) | bad p | bad xi | ord | bad rank | good p | good xi | ord | good rank | char-0 conclusion
common core C       | d=7     | 43    | 4      | 7   | joint 17 | 127    | 4       | 7   | joint 18  | order-7 sector certified by (127,4)
full code W         | (15,5)  | 31    | 10     | 15  | W+JW 13  | 61     | 16      | 15  | W+JW 14   | order-15 sector certified by (61,16)
full code W         | (33,11) | 67    | 40     | 11  | W+JW 31  | 199    | 125     | 11  | W+JW 32   | order-11 sector certified by (199,125)
```

Targets: common core joint rank r−3 = 18 (d=7); full-code dim(W+JW) = r−1
(14 for r=15; 32 for r=33). In each row the good cell attains the target
at the SAME exact root order, so by the good-reduction lemma the
characteristic-zero rank is at least the target; maximality gives equality.
The bad cells are bad finite-field reductions (a minor's algebraic norm
divisible by the bad prime), not characteristic-zero facts.

Why a modular failure is allowed (§10): a nonzero algebraic
determinant/minor may reduce to zero modulo a prime dividing its algebraic
norm — rank drop mod p does not imply rank drop in characteristic zero.
Conversely one full-rank good reduction proves the rank. Concrete pair:
(d,n0) = (7,1): p=43, ξ=4 drops; p=127, ξ=4 (same exact order 7) is full.
