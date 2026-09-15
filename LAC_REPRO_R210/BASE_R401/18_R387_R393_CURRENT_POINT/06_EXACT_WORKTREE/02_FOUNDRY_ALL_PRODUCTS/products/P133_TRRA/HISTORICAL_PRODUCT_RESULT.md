# Product result — P133_TRRA v0.1

**Product:** Transient-Risk Resolution Allocator  
**Parents:** DTRM + ACRA  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Fine sensing resolution is assigned to state directions with the largest finite-horizon action-flip exposure.

## Measured evidence

- **transient_index_by_direction**: `{'state_x1': 0.8, 'state_x2': 1.4266455227241104}`
- **fine_regions**: `['state_x2']`
- **status**: `TRANSIENT_DECISION_RISK_ROUTES_RESOLUTION_BUDGET`
- **tests**: `6/6`

## Claim boundary

Direction scores depend on the declared linearized dynamics, uncertainty radius, horizon, and decision gap.
