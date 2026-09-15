# P091_DCBT — Decision Compression Budget Tipping

**Composition:** DSBC + TDSX

Converts DSBC regret tolerance into an explicit state-budget tipping surface.

## Benchmark

Four belief states require regret tolerance 0.60 before the declared <=2-state budget is reached; realized max regret at tipping is 0.60.

## Claim boundary

The result is conditional on the supplied beliefs, utilities, and declared tolerance grid.

## Verification

6/6 product tests passed.
