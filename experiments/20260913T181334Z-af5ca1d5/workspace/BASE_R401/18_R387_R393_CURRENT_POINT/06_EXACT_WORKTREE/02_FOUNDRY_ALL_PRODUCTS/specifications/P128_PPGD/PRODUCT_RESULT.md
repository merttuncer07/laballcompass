# Product result — P128_PPGD v0.1

**Product:** Percolation Path Guard Designer  
**Parents:** PCBE + CSID  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Cell failures are scored by lost effective conductance plus loss of breakthrough status before guard-budget optimization.

## Measured evidence

- **baseline_conductance**: `3.5`
- **consequence_by_cell**: `{'1,0': 3.1607142857142856, '1,1': 3.6666666666666665, '1,2': 3.1607142857142865, '0,1': 0.0}`
- **selected_safeguards**: `['protect_1,1']`
- **status**: `BREAKTHROUGH_PATH_CONSEQUENCES_ROUTED_TO_GUARDS`
- **tests**: `6/6`

## Claim boundary

Cell replacement is a declared physical stress, not a causal failure-rate estimate.
