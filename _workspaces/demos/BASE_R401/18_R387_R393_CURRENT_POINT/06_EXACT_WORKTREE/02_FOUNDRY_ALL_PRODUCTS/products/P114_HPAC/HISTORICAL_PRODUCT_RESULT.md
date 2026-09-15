# Product result — P114_HPAC v0.1

**Product:** Hidden-Population Acquisition Controller  
**Parents:** MLHPE + AICC  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Turns a Chapman hidden-population estimate and its sampling uncertainty into a downstream capacity-boundary measurement decision.

## Measured evidence

- **near_current_action**: `HOLD`
- **near_chosen_channel**: `precise`
- **near_status**: `MEASURE`
- **far_chosen_channel**: `None`
- **status**: `MEASURE`
- **tests**: `6/6`

## Claim boundary

The Gaussian belief adapter uses the Chapman standard error and a declared linear expand/hold utility around a capacity threshold; it is not a full Bayesian posterior over capture dependence.
