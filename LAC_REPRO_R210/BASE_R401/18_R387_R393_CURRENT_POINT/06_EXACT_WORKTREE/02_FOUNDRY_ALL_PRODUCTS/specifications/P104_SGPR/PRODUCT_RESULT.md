# Product result — P104_SGPR v0.1

**Product:** Support-Gated Private Release  
**Parents:** OWS + DTPR  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Enforces statistical-support validity before spending privacy budget. A fragile target reweighting is blocked before DTPR executes; usable support can release only the declared private action.

## Measured evidence

- **usable_ess_fraction**: `0.9999999999999997`
- **released_action**: `HIGH`
- **epsilon_spent**: `20.0`
- **remaining_epsilon**: `5.0`
- **fragile_case_epsilon_spent**: `0.0`
- **tests**: `6/6`

## Claim boundary

Privacy does not certify statistical validity, and OWS does not certify the externally declared global sensitivity of the DTPR score.
