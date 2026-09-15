# Connected Deployable Bottleneck Locator

CDBL turns **IM-141 → IM-023** into a time-aware network product. It distinguishes nominal stock,
active stock, and the amount that can actually reach a target through capacity-, yield-, and
deadline-constrained paths. It then adds the same small capacity increment to each edge and active
stock location, re-solves the network, and ranks the current bottleneck by marginal delivered gain.

The core is a generalized time-expanded linear program, not a count of inventory adjacent to a
named bottleneck.

## Run

```powershell
python -m unittest -v test_cdbl.py
python demo_deployable_network.py
```

## Product boundary

v0.1 handles one divisible material and deterministic capacity/yield/lead time. Next layers are
multi-commodity compatibility, dated demand, stochastic disruption, shared capacities, integer
activation decisions, and intervention cost.
