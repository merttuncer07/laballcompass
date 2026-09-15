# Product result — P103_CFAI v0.1

**Product:** Circular-Flow Audit Allocation  
**Parents:** HFAD + BICC + ACRA  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Turns HFAD circulation energy into a black-box audit target, measures edge replacement influence with BICC, and allocates scarce sensing/audit resolution with ACRA.

## Measured evidence

- **baseline_cycle_energy**: `300.0`
- **edge_effects**: `[166.66666666666666, 19.666666666666572, 9.916666666666742]`
- **fine_edge**: `0`
- **budget**: `1.0`
- **tests**: `6/6`

## Claim boundary

Circulation is a flow-topology signal, not a fraud label. The current benchmark uses empirical influence only because no global edge-flow bound is supplied.
