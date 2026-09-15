# P027 IDAC v0.1 — Integral Deployability Audit Certificate

## Composition

CDBL continuous time-expanded deployment LP -> RIC exact total-unimodularity/integrality audit.

IDAC determines when a continuous deployment result can be interpreted as a discrete-unit optimum without silently rounding. It reconstructs CDBL's LP shell, checks total unimodularity and integer right-hand sides, and separately reports the observed LP/integer comparison.

## Benchmark

Small exact time-expanded networks:

- unit-yield + integer-RHS case: TU `true`, LP integral `true`, integrality gap `0`, theorem certificate `true`, deployable `30`
- fractional yield `0.5`: TU fails, so no theorem is claimed even though this particular LP optimum happens to be integral
- fractional yield `0.75`: TU fails and the observed LP solution is fractional with integrality gap `0.25`
- fractional active stock: matrix remains TU but integer-RHS condition fails, so no integrality theorem is claimed

## Claim boundary

Exact TU enumeration is intentionally limited to small matrices. Failure to obtain a TU certificate is not proof that every optimum is fractional, and an integral solution in one instance is not a structural integrality theorem.
