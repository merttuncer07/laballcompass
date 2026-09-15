# Product result — P132_CARA v0.1

**Product:** Calibration-Aware Resolution Allocator  
**Parents:** CWC + ACRA  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Scarce measurement resolution is routed to streams with the largest calibrated coverage-deficit consequence.

## Measured evidence

- **calibration_consequence**: `{'critical': 0.6400000000000002, 'stable': 0.024400000000000022, 'benign': 0.0}`
- **fine_regions**: `['critical']`
- **total_decision_loss**: `0.06160200000000005`
- **status**: `CALIBRATION_DEFICIT_ROUTES_RESOLUTION_BUDGET`
- **tests**: `6/6`

## Claim boundary

Calibration consequence uses the declared target, window, and interval-score scaling; it is not a universal loss function.
