# Wasserstein Decision-Tipping Geodesic

**Status:** PROMOTED v0.1

**Composition:** WBDP + TDSX

Measures where a downstream decision first flips along a declared Wasserstein displacement path and reports W2 distance from the source.

## Validation

The product has a deterministic synthetic/adversarial benchmark in `BENCHMARK_RESULT.json` and a dedicated unit-test file. Claims are limited by the explicit contract returned by the implementation.
