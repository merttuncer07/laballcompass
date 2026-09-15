# Product result — P105_PRAS v0.1

**Product:** Private Regret-Aware Selection  
**Parents:** ACSA + DTPR  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Uses ACSA internally on a sensitive protected candidate family, then releases only a candidate name via DTPR exponential selection; raw protected losses and holdout-best identity are not returned.

## Measured evidence

- **search_selected**: `A`
- **private_protected_release**: `B`
- **epsilon_spent**: `20.0`
- **remaining_epsilon**: `5.0`
- **utility_sensitivity**: `0.1`
- **tests**: `6/6`

## Claim boundary

The utility-sensitivity bound is caller-supplied and must be valid under the neighboring-dataset definition. Internal access to protected losses remains trusted computation.
