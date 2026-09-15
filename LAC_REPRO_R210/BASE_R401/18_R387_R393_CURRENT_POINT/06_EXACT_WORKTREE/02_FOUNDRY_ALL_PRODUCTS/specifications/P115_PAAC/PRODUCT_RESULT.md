# Product result — P115_PAAC v0.1

**Product:** Priority Appraisal Acquisition Controller  
**Parents:** PRIU + AICC  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Derives the first funded-asset value on a declared grid that permits protected financing, then values appraisal channels only by their ability to resolve that financing boundary.

## Measured evidence

- **near_current_action**: `DO_NOT_FUND`
- **near_chosen_channel**: `field`
- **near_status**: `APPRAISE`
- **far_chosen_channel**: `None`
- **status**: `APPRAISE`
- **tests**: `6/6`

## Claim boundary

The threshold is grid-relative and uses the declared single-scenario appraisal adapter; measurement costs must be expressed in the same utility scale.
