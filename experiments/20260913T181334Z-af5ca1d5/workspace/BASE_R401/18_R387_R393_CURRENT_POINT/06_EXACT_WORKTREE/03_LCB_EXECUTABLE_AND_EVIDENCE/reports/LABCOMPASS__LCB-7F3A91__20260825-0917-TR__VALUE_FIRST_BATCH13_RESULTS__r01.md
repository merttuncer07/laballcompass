# Value-first benchmark batch 13

## RX-188 — RiskShiftContractGuard
Downside-only support creates a put-like private payoff: chosen volatility rises .5 -> 5.0 and severe
shortfall 8.1% -> 29.4%. Adding upside participation lowers chosen volatility to 1.0, shortfall to
~.36%, and median counterparty transfer cost 1.513 -> .008. Promote.

## RX-136 — DelayedVerificationIncentiveGate
Nominal reward schedule is unchanged. Audit information without payoff consequence leaves median
misreport at 1.0. A verifiable future clawback reduces it to .433 (-56.7%). If the audit signal is
uninformative about misreport, behavior does not change. Promote.

## RX-045 — SolverCertificateAudit
Under a deliberately unresolved one-iteration solve, generic solver status is unknown on every case.
Independently normalized primal/Farkas witnesses classify all constructed feasible, degenerate-feasible
and infeasible instances correctly, matching the normal full solver. Promote as assurance core, not
as a replacement for normal solving.

## RX-056 — StrategicCapacityResponseGuard
Across a randomized Braess family, the added link worsens self-interested equilibrium in 99.8% of
cases; median harm is 15.72 time units/user. System-optimal routing is non-worse in 100%, isolating
strategic rerouting as the failure mechanism. Promote.

## RX-165 — MeasurementInvarianceGate
The conceptual warning is valid, but this tested shell does not produce product value. Both groups
have alpha >.96, yet naive/group-z cross-group ranking is already ~.992 AUC; group-specific map
correction improves by only .00035 AUC. Close this formulation.
