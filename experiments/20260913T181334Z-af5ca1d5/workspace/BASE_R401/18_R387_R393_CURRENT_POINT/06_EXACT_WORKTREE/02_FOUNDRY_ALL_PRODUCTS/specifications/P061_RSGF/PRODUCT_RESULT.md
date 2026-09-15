# Remote-Synchronization-Gated Firewall

**Status:** PROMOTED v0.1

**Composition:** RSPI + MIFF

RSPI gates suspect modules from remote-synchronization evidence; MIFF computes a minimum-cost cut on a separately declared information-flow graph.

## Validation

The product has a deterministic synthetic/adversarial benchmark in `BENCHMARK_RESULT.json` and a dedicated unit-test file. Claims are limited by the explicit contract returned by the implementation.
