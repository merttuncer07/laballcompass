# Product result — P126_TRGD v0.1

**Product:** Transient Risk Guard Designer  
**Parents:** DTRM + CSID  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Finite-horizon action-flip exposure from each uncertainty channel is converted into safeguard consequence.

## Measured evidence

- **consequence_by_channel**: `{'x1_channel': 0.8, 'x2_channel': 1.4266455227241104}`
- **selected_safeguards**: `['protect_x2_channel']`
- **baseline_index**: `1.5263000182023017`
- **status**: `TRANSIENT_DECISION_RISK_ROUTED_TO_GUARDS`
- **tests**: `6/6`

## Claim boundary

DTRM indices are local to the declared linear shell, horizon, uncertainty radius, and decision gap; safeguard failure probabilities are declared inputs.
