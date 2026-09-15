# P029 RATR v0.1 — Resilience-Aware Target Reduction

## Composition

TWMR target-weighted coordinate reduction -> HMRM current hidden-mode recovery guard.

RATR uses the same coordinate-deletion shell as TWMR, but a candidate reduction is admissible only if it preserves HMRM's current joint resilience-alert status. Among admissible subsets it minimizes TWMR target impulse-response error. If the state budget cannot preserve the current resilience status, it refuses to claim a safe reduction.

## Benchmark

Three-state synthetic system with a slow mode that is invisible to the input→protected-output impulse sequence but currently consequence-bearing:

- unconstrained TWMR retained `fast_target + aux`
- unconstrained target-relative error: `0`
- full HMRM joint alert: `true`
- unconstrained reduced HMRM joint alert: `false`
- RATR retained `fast_target + slow_hidden`
- RATR target-relative error: `0.0564748094`
- RATR reduced HMRM joint alert: `true`

Thus the guard exposes a real target-fidelity/resilience trade-off instead of hiding the slow current risk.

## Claim boundary

Coordinate-deletion benchmark. RATR preserves HMRM's current joint-alert classification, not the complete modal spectrum, every recovery time, or arbitrary future trajectories.
