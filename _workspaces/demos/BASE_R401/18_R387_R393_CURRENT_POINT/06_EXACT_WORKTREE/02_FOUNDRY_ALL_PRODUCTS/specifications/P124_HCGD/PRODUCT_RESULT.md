# Product result — P124_HCGD v0.1

**Product:** Hedge Component Guard Designer  
**Parents:** DHCC + CSID  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Removes each hedge instrument, recalibrates the hedge, and converts the resulting validation decision-loss increase into safeguard consequence.

## Measured evidence

- **baseline_loss**: `0.08628435339574686`
- **consequence_by_hedge**: `{'core': 2.16333039994999, 'secondary': 0.25266190993036186, 'noise': 0.00011757483755052422}`
- **selected_safeguards**: `('protect_core',)`
- **status**: `HEDGE_AVAILABILITY_CONSEQUENCES_ROUTED_TO_GUARDS`
- **tests**: `6/6`

## Claim boundary

Instrument unavailability is a declared counterfactual; liquidity/default mechanisms are not inferred by DHCC.
