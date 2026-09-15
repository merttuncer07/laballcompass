# P145 RTHA — Restart-Threshold Holdout Audit

Parents: RTO -> ACSA.

Restart thresholds are evaluated batch-by-batch with RTO on a selection workload and an untouched workload, then audited as a visible candidate family by ACSA.

Benchmark: heavy-tail selection workload chooses threshold 3 with expected time 2.832 versus no-restart 9.562. On the light-tail holdout, threshold 3 remains finite but costs 29.187 versus no-restart 3.846. Protected regret is 25.341 and ACSA reports adaptive selection regret.

Claim boundary: RTO's renewal/fresh-draw assumption remains required for each restart-policy evaluation.

Status: WORKING_COMPOSITION; 6/6 tests.
