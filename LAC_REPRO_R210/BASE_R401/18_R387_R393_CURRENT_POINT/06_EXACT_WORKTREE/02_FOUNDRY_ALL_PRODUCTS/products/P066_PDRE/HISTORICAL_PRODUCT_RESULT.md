# Private Decision-Relevant Explorer

**Status:** PROMOTED v0.1

**Composition:** DRE + DTPR

Computes exploration value internally and privately releases only the selected measurement arm using the exponential mechanism and an externally supplied sensitivity bound.

## Validation

The product has a deterministic synthetic/adversarial benchmark in `BENCHMARK_RESULT.json` and a dedicated unit-test file. Claims are limited by the explicit contract returned by the implementation.
