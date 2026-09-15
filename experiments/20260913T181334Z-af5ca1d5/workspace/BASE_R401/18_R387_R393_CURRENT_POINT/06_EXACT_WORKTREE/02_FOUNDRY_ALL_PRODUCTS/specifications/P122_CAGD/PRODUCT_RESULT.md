# Product result — P122_CAGD v0.1

**Product:** Control Actuator Guard Designer  
**Parents:** CCVC + CSID  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Measures each actuator failure by the loss of conservation-constrained inward viability margin and allocates safeguard budget to the actuator whose loss can make the boundary nonviable.

## Measured evidence

- **baseline_minimum_margin**: `0.43999999999999995`
- **margin_by_actuator_failure**: `{'strong': -0.16000000000000003, 'weak': 0.19999999999999996}`
- **consequence_by_actuator_failure**: `{'strong': 2.2, 'weak': 0.24}`
- **selected_safeguards**: `('protect_strong',)`
- **status**: `ACTUATOR_VIABILITY_CONSEQUENCES_ROUTED_TO_GUARDS`
- **tests**: `6/6`

## Claim boundary

The consequence scaling from negative viability margin is declared and local to the audited boundary state.
