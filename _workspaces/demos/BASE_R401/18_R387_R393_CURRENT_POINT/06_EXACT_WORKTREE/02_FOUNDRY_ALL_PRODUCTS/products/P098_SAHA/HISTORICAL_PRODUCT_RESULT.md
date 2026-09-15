# Product result — P098_SAHA v0.1

**Product:** Specification-Adaptive Holdout Audit  
**Parents:** SCE + ACSA  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Closes the explicit SCE → ACSA frontier by freezing each valid control-set specification after learning, emitting casewise selection/holdout prediction losses, and auditing the adaptively selected specification on untouched data.

## Measured evidence

- **selection_selected**: `with_z`
- **holdout_best**: `simple`
- **selected_holdout_regret**: `9.0`
- **tests**: `6/6`

## Claim boundary

v0.1 deliberately fixes outcome, treatment, and sample rule and audits the control-set search dimension. Expanding all SCE dimensions requires a common protected prediction target rather than silently comparing different outcomes.
