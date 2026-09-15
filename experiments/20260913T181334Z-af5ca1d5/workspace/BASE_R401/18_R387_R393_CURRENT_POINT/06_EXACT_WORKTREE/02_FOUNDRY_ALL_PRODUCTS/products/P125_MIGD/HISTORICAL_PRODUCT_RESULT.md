# Product result — P125_MIGD v0.1

**Product:** Mortgage Intervention Guard Designer  
**Parents:** MCRIS + CSID  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Turns failure of individual intervention levers into lost mortgage-intervention net value and directs safeguard budget to the most economically consequential lever.

## Measured evidence

- **full_intervention_net_value**: `36430624.29743956`
- **consequence_by_lever**: `{'performing_default': 31580332.556986883, 'performing_delinquency': 9696603.212562785, 'delinquent_default': 9006969.602709278, 'delinquent_cure': 4202412.552349672}`
- **selected_safeguards**: `('protect_performing_default',)`
- **status**: `MORTGAGE_INTERVENTION_LEVER_FAILURES_ROUTED_TO_GUARDS`
- **tests**: `6/6`

## Claim boundary

Lever-failure probabilities and guard effectiveness are declared; the benchmark does not estimate implementation-failure rates.
