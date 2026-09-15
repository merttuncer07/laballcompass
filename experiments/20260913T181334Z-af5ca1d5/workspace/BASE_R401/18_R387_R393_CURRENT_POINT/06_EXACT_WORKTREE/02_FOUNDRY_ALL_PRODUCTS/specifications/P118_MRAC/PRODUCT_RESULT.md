# Product result — P118_MRAC v0.1

**Product:** Mortgage Risk Acquisition Controller  
**Parents:** MCRIS + AICC  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Finds the default-rate level at which a declared mortgage intervention becomes net-positive and values additional default-rate measurement near that intervention boundary.

## Measured evidence

- **near_current_action**: `DO_NOT_INTERVENE`
- **near_chosen_channel**: `sample`
- **near_status**: `MEASURE_DEFAULT_RATE`
- **far_chosen_channel**: `None`
- **status**: `MEASURE_DEFAULT_RATE`
- **tests**: `6/6`

## Claim boundary

The default-rate belief is a one-dimensional adapter with other transition rates and intervention terms held fixed.
