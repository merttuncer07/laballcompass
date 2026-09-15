# Product result — P117_MFAC v0.1

**Product:** Market Forecast Acquisition Controller  
**Parents:** MCPR + AICC  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Finds the first declared demand level that produces shortage under market clearing, then buys a demand measurement only when forecast uncertainty can cross that scarcity boundary.

## Measured evidence

- **near_current_action**: `NORMAL_DISPATCH`
- **near_chosen_channel**: `fast`
- **near_status**: `MEASURE_DEMAND`
- **far_chosen_channel**: `None`
- **status**: `MEASURE_DEMAND`
- **tests**: `6/6`

## Claim boundary

The shortage threshold is grid-relative and conditional on fixed offer quantities/prices and the declared scarcity-price convention.
