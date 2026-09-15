# P137 MPHA — Memory-Policy Holdout Audit

Parents: ATRC -> ACSA.

ATRC memory-policy variants are treated as a visible candidate family. Each policy is run unchanged on a selection stream and an untouched holdout stream; casewise prediction losses feed ACSA.

Benchmark: selection chooses `short` memory (loss 0.06076 vs 0.14715). Untouched holdout chooses `long` (0.03268 vs short 0.13802). Selected-policy holdout regret is 0.10534 and ACSA reports `ADAPTIVE_SELECTION_REGRET_DETECTED`.

Claim boundary: this audits policy selection across declared streams; it does not prove either retention policy is universally optimal.

Status: WORKING_COMPOSITION; 6/6 tests.
