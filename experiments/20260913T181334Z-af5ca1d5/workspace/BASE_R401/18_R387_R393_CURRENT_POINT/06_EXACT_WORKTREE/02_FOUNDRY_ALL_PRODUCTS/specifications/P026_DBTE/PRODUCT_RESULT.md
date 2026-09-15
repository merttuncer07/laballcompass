# P026 DBTE v0.1 — Deployable Bottleneck Tipping Explorer

## Composition

CDBL deadline-aware deployability LP -> TDSX capacity tipping surface.

DBTE asks which capacity change actually moves delivered resource across a declared target after topology, lead-time, yield, active-stock, and deadline constraints. It therefore distinguishes nominal capacity expansion from expansion of the true deployable bottleneck.

## Benchmark

Three-node synthetic chain:

- baseline deployable amount: `30`
- delivery threshold: `50`
- nearest tipping point: `wide=80`, `narrow=50`
- deployable amount at tipping point: `50`
- increasing only the already-wide upstream edge produced no decision flip
- an edge with lead time `4` under horizon `3` remained deployable `0` even when its nominal capacity increased to `100`

## Claim boundary

Synthetic network benchmark. The tipping point is conditional on the declared network, horizon, grid, active stock, edge capacities, lead times and conversion yields. It is not a general supply-chain capacity estimate.
