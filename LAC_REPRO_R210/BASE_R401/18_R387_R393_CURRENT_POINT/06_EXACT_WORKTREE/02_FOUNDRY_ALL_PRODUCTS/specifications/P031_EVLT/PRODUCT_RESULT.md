# P031 EVLT v0.1 — Evidence-Weighted Liquidity Triage

## Capability

EVLT combines REL's posterior over relational discrepancy explanations with LCM's constrained liquidity-allocation engine. It selects which claims to audit under a finite verification budget by recomputing posterior-expected deployable liquidity for every feasible audit subset.

An audited claim becomes verified only in posterior scenarios where the claim is not a culprit. This explicitly separates "suspicious" from "likely to verify clean" and prevents a high culprit probability from being misused as a funding-success probability.

## Benchmark result

In the fixed synthetic benchmark, claim A has face value 300 but REL assigns it culprit probability 0.997856. Claims B and C each have clean probability 0.998928 and standalone expected liquidity uplift 59.9357.

With one audit slot EVLT chooses B/C rather than the much larger nominal A. With two slots it does **not** treat B+C as 119.8714 of additive value: the shared warehouse capacity and anchor cap make their liquidity effects non-additive. Exact portfolio re-optimization therefore selects one of B/C plus A, yielding expected deployable liquidity 60.0429.

## Claim boundary

REL probabilities remain conditional on its enumerated non-empty culprit-set hypothesis space. EVLT is therefore a conditional audit-triage engine, not an unconditional fraud-probability estimator. Audit outcomes are modeled as: clean scenario -> successfully verified through the declared verifier; culprit scenario -> remains unverified. LCM channel/capacity/anchor constraints are rerun for every posterior scenario and audit subset.

## Verification

6/6 product tests pass.
