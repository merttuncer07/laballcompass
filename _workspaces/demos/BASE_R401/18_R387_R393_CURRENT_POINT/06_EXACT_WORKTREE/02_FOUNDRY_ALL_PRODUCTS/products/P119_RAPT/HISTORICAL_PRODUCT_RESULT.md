# Product result — P119_RAPT v0.1

**Product:** Rerandomization Acceptance-Pool Tipping  
**Parents:** CBAC + TDSX  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Stress-tests rerandomization strictness until the accepted randomization pool falls below a declared diversity floor.

## Measured evidence

- **baseline_acceptance_fraction**: `0.05`
- **baseline_pool_size**: `50`
- **minimum_pool_size**: `20`
- **tipping_acceptance_fraction**: `0.01`
- **tipping_pool_size**: `10`
- **status**: `POOL_DIVERSITY_TIPPING_FOUND`
- **tests**: `6/6`

## Claim boundary

The pool-size floor is a design requirement, not a universal causal-validity threshold; the tipping value is relative to the declared randomization-draw count.
