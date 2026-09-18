# Q195 Provenance V3

## What V3 used (and banned)

V1 harness and V2 provisional sweep: NOT used as mathematics (per order).
V1/V2 packages sealed unchanged. V1 suffix-difference Gamma: SUPERSEDED by
the exact centered interval derivation (Phase 1). V1 width-3 labels and
d=5 histograms: DEMOTED to historical nearby-code data (Phase 13) — built
from the wrong packet object; regeneration from exact packets is future
work, not done here.

## What V3 established

- Older files absent locally and in all stored history (documented search).
- Phase-1 identities proved + machine-checked (all ξ, two primes).
- Weighted reversal DERIVED (no recovered formula existed): J[i→j] =
  ξ^{P_j−P_i}[j→i]; πJ = Ĵπ and J² = I unit-tested; J/Ĵ distinction
  documented (Ĵ = ξx^{−2}J, Ĵ1 ≠ 1).
- Source-faithful F*/C/b_in/b_out (V2 chronology re-asserted in driver).
- Historical checkpoints: 208/210 cells PASS; 2 frequency cells fail
  ((15,5,31,10), (33,11,67,40)), both via boundary (b_in-side) directions
  with full core rank; (15,9),(25,5),(35,14) NOT RECONSTRUCTIBLE.
- True sweep: 755/756 cells joint == r−3; single failure (7,1,43,4),
  independently confirmed via sympy GF(43) (joint rank 17).
- Formal lift transverse on ALL 756 surveyed cells, including the failing
  one: formal-zero coexists with kerPi-nonzero there — the Q194 distinction
  is computationally confirmed, and the equivalence lemma's hypotheses are
  exactly what separate the two regimes.

## Implementation defects found and fixed (harness only, never the math)

- padd() kept phantom {0:0} seeds (dict inequality on equal polys).
- Phase-4 test encoded x^{−2} as +x^{r−2} (sign; caught at h = 0).
- Driver drafting debris removed before runs; failing cells investigated,
  never tuned (conventions frozen before the sweep).

## Spec truncation note

The Phase-12..14 instructions arrived truncated mid-lemma; completed as:
equivalence lemma (above scope), no width-3 proof attempted, V3 package
per the listed contents, standalone-tested, this report.

## Mathematical status

Q195 general theorem: OPEN. V3 finite evidence is trustworthy exactly to
the extent logged: 755/756 + 208/210 with every failing cell named.
