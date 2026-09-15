# Product result — P121_MSGD v0.1

**Product:** Market Supply Guard Designer  
**Parents:** MCPR + CSID  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Re-clears the market under each offer outage, prices the resulting unserved demand as consequence, and spends safeguard budget on the most consequential supply block.

## Measured evidence

- **baseline_unserved**: `0.0`
- **consequence_by_offer**: `{'base': 4000.0, 'mid': 2000.0, 'backup': 0.0}`
- **selected_safeguards**: `('protect_base',)`
- **expected_residual_loss**: `480.0`
- **status**: `MARKET_SHORTAGE_CONSEQUENCES_ROUTED_TO_GUARDS`
- **tests**: `6/6`

## Claim boundary

Offer-outage probabilities and shortage unit cost are declared scenario inputs; this does not infer physical outage rates.
