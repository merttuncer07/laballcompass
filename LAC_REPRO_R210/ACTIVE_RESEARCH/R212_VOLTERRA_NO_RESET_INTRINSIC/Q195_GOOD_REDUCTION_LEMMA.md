# Good-Reduction Lemma (V4 §2)

Matrices in the Q195 experiment have entries in Z[1/2][ξ,ξ^{−1}] after
fixing (d, n0), with ξ^r = 1. Let s | r and ζ_s a primitive complex s-th
root of unity. Let M_s = M(ζ_s) be any tested matrix.

## Lemma — one good modular reduction certifies characteristic-zero rank

Let k be the desired rank. Suppose there is an odd prime p with p ∤ s and
an element a ∈ F_p^× of exact order s such that the reduction M(a) mod p
has rank k. Then rank_{Q(ζ_s)} M(ζ_s) ≥ k. If k is maximal possible,
equality follows.

Proof: if characteristic-zero rank were < k, every k×k minor would vanish
at ζ_s. After clearing powers of X and powers of 2, every such minor
polynomial is divisible over Q[X] by Φ_s(X). By Gauss's lemma, after
clearing denominators the integer polynomial is divisible by Φ_s up to an
integer scalar. Since p ∤ 2s and a has exact order s, Φ_s(a) = 0 mod p
(a is a root of Φ_s mod p: its order is exactly s, and p ∤ s keeps Φ_s
separable mod p). Hence every k×k minor vanishes at a mod p,
contradicting rank k. ∎

Consequence used throughout V4: a modular rank DROP proves nothing about
characteristic zero; one full-rank good reduction at the same exact root
order proves the characteristic-zero rank is at least that large. Rank is
Galois-invariant among primitive s-th roots, so one good exact-order-s
reduction certifies the whole primitive order-s sector.
