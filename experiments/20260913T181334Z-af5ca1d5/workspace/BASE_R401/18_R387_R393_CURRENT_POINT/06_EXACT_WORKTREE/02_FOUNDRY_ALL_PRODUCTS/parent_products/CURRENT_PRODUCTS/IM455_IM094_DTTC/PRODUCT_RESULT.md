# IM-455 → IM-094 product result: Decision-Targeted Trigger Channel Designer v0.1

DTTC is now executable software. It takes one common event field, candidate trigger channels, a
protected action definition, asymmetric action-error costs, verification cost, and manipulation
exposure. It searches candidate thresholds, ranks complete trigger policies, and returns the policy
with the lowest declared operational objective.

## Common-field construction result

The first product evaluation generated 300,000 deployment cases with a shifted loss distribution.
The local sensor was precise before manipulation but could be increased in 40% of non-event cases;
the realized manipulation rate was 34.47%. The regional sensor was noisier but independent.

| Candidate | Correlation | Threshold | FN | FP | Verification | Manipulation | Total objective |
|---|---:|---:|---:|---:|---:|---:|---:|
| Regional | 0.8637 | 1.1590 | 0.0180 | 0.1245 | 0.04 | 0.00 | **0.2547** |
| Local | 0.5501 | 1.3141 | 0.0032 | 0.3472 | 0.01 | 0.20 | 0.5733 |

The tool selected the regional channel. The important result is not that regional signals are always
better; it is that channel selection, threshold choice, verification, and manipulation exposure are
now one executable decision object instead of separate qualitative comments.

## Working software

- reusable candidate/threshold optimizer;
- asymmetric false-negative and false-positive costs;
- verification and manipulation terms;
- correlation retained as a diagnostic rather than a veto or objective;
- common-field simulation with saved results;
- three automated tests, all passing.

## Next construction layer

Separate policy fitting from deployment evaluation, add spatial and temporal basis-risk terms, and
model actors who change their behavior after the trigger rule is published. Then expose the engine
through a CSV/config CLI for actual candidate-index datasets.
