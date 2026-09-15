# IM-445 → IM-085 product result: Contract Safeguard Independence Designer v0.1

CSID is an executable portfolio designer for contracts whose visible decision margin may be aligned
while hidden effort, reporting, or relocated decision rights remain exposed.

## Construction result

The first scenario used three failure modes and five safeguards under budget 7. A conventional
calculation treated every named safeguard as independent and selected:

- sales-rebate monitor;
- revenue-share audit;
- decision-right exception review.

The first two read the same sales-system evidence. The optimistic model reported objective 11.956.
When their common evidence family was represented, the same portfolio's real objective became 16.60.

CSID selected:

- sales-rebate monitor (`sales_system` evidence);
- decision-right exception review (`governance` evidence).

It spent 5 rather than automatically exhausting the budget, obtained expected residual loss 10.14,
and total objective 15.14. Relative to the naive portfolio under common-evidence reality, the working
objective improved by **8.80%**.

## Working software

- explicit failure probability and consequence model;
- safeguard cost and failure-specific coverage;
- evidence-family/common-mode representation;
- exhaustive feasible-portfolio selection under budget;
- transparent naive-versus-family-aware comparison;
- four automated tests, all passing.

## Next construction layer

Add uncertain probability/coverage ranges and recompute actor effort after each proposed contract.
That will connect safeguard selection directly to endogenous behavior instead of treating failure
probabilities as fixed inputs.
