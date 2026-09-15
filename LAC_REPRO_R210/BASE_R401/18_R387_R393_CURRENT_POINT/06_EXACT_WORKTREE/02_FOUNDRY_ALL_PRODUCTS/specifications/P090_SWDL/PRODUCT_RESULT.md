# P090_SWDL — Support-Weighted Decision Loss

**Composition:** OWS + DLEW

Uses OWS as an overlap/ESS gate and evaluates DLEW-style downstream regret under target importance weights.

## Benchmark

Source selection `source_model` flips to target-weighted `target_model`; target regret 0.6897 -> 0.3103; ESS fraction 0.2056.

## Claim boundary

Target importance weights must be externally justified; usable ESS does not prove transportability.

## Verification

6/6 product tests passed.
