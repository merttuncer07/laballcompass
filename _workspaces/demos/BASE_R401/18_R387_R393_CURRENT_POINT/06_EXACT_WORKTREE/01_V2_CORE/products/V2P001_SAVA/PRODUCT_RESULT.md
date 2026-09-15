# V2P001 SAVA — Shared-Capacity Audit Value Allocator

## Composition

LCB `SharedCapacityAllocatorV0` + Foundry `P031 EVLT`.

EVLT contributes posterior scenario semantics: an audited claim becomes usable only in scenarios where it is clean. The LCB kernel contributes a monotone submodular rank oracle for overlapping capacity pools. SAVA therefore allocates verification capacity without treating two claims drawing on the same warehouse, anchor, reviewer, or funding pool as independent additive value.

Small portfolios use exact posterior subset re-optimization. Large portfolios route to a continuous polymatroid allocation instead of pretending exponential enumeration scales.

## Strength

It produces a standalone audit-allocation decision and also acts as a component for LCM/VPRL/VCPA liquidity products.

## Weakness / boundary

Posterior culprit scenarios, pool contributions, capacities, and liquidity-per-unit remain declared model inputs. The scalable route is a divisible-capacity allocation, not an exact discrete audit-subset theorem. A negative field result narrows that operational shell and triggers calibration/router work; it does not delete the mechanism.

## Verification

Six invariant and contrast tests accompany the implementation.
