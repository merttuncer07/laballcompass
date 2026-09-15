# P134 REIG v0.1 — PRODUCT RESULT

Status: **WORKING_COMPOSITION**

Parents: **REL → EBC**

## New capability

EBC already downweights historical estimates that conflict with the current estimate, but it has no notion of cross-source relational integrity. REIG first uses REL to detect and localize declared consistency violations among historical sources, then gates source-specific EBC borrowing power before EBC performs its own compatibility weighting.

The integrity gate activates only when at least one declared relation is violated. When no violation is observed, original historical borrowing powers pass through unchanged.

## Benchmark

Historical values:

- A = 0.10
- B = 0.12
- C = 1.05

Declared consistency tolerance is 0.20. Relations A-C and B-C violate the declared constraints. REL assigns C marginal suspect mass **0.972495** within its enumerated culprit hypothesis space; A and B each receive **0.026488**.

Declared maximum borrowing power is 1.0 for every historical source. REIG therefore maps:

- A → **0.973512**
- B → **0.973512**
- C → **0.027505**

With current estimate 1.0 ± 0.5 SE:

- ordinary EBC posterior = **0.712334**
- integrity-gated EBC posterior = **0.423174**

For a declared decision threshold of 0.60, the downstream action flips from **accept** under ungated borrowing to **reject** under integrity-gated borrowing.

The total EBC borrowing-precision ratio remains capped at 2.0 in both cases; the difference comes from *which historical sources receive the borrowed precision*, not from bypassing EBC's cap.

## Claim boundary

REL marginal suspect mass is **not** an unconditional probability of fraud, falsification, or bad data. It is conditional on REL's declared one-or-more-culprit hypothesis space and consistency model. REIG uses it only through an explicit borrowing-power policy:

`gated_power = declared_power × (1 - conditional_suspect_mass)^integrity_exponent`

No declared relational violation → no integrity penalty.

## Verification

`6 passed` in isolated P134 regression.
