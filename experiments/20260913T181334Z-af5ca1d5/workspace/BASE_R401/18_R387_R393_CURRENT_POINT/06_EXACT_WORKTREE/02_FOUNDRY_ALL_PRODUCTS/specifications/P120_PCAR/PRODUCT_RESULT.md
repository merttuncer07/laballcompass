# Product result — P120_PCAR v0.1

**Product:** Private Calibration Action Release  
**Parents:** CWC + DTPR  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Runs calibration-width control internally, counts coverage misses with sensitivity one, and releases only a private HOLD/WIDEN action rather than raw calibration data.

## Measured evidence

- **undercovered_miss_count**: `18`
- **undercovered_private_action**: `WIDEN`
- **remaining_epsilon**: `5.0`
- **well_covered_private_action**: `HOLD`
- **status**: `PRIVATE_CALIBRATION_ACTION_RELEASED`
- **tests**: `6/6`

## Claim boundary

Differential privacy applies to the released miss-count action under the declared neighboring-dataset definition; internal CWC state remains trusted computation.
