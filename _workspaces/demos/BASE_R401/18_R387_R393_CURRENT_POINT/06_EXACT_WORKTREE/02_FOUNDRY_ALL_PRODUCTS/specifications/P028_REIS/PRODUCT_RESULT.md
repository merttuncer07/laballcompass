# P028 REIS v0.1 — Relational Evidence Impact Safeguards

## Composition

REL discrepancy localization -> BICC empirical downstream replacement impact -> CSID safeguard portfolio.

REIS separates two questions that can disagree: which record is most likely to explain the discrepancy, and which suspicious record has the largest expected downstream consequence if it is wrong. Safeguard budget is allocated using posterior probability multiplied by an explicitly aligned empirical consequence scale.

## Benchmark

Synthetic three-record discrepancy:

- REL posterior culprit probability: A `0.97250`, B `0.02649`, C `0.02649`
- empirical BICC consequence: A `1.7464`, B `132.2120`, C `0.6021`
- posterior-impact risk: A `1.6984`, B `3.5020`, C `0.01595`
- posterior-only priority: A first
- impact-aware priority: B first
- with one-audit budget, CSID selected `audit_B`

Thus the most probable culprit was not the highest expected downstream-impact target.

## Claim boundary

REL probabilities are conditional on its enumerated non-empty culprit-set hypothesis space. BICC replacement effects are empirical sensitivity measurements of the supplied scalar function, not causal effects. CSID inherits whatever operational-loss semantics that scalar consequence function is given.
