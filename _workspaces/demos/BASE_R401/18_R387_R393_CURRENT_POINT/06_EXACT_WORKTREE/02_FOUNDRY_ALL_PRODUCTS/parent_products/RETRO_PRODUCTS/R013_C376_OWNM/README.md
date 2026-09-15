# Ownership Wedge Network Mapper

OWNM is an independent product from **R-013 / C-376 / E-749–E-752**. C-376 was historically merged
into IM-008, but dual-class shares, pyramids, and cross-ownership define a concrete governance audit
with its own user and output contract.

The mapper computes economic exposure linearly through the ownership network while propagating
voting control through threshold crossings. Once a company is controlled, its downstream votes
become commandable in the next control round. It reports ultimate cash exposure, commanded votes,
control round, control-to-cash wedge, controlled assets per cash-at-risk, and strong cross-ownership
components.

## Run

```powershell
python -m unittest -v test_ownm.py
python demo_control_wedge.py
```

## Boundary

v0.1 assumes known deterministic holdings and simple majority thresholds. Next layers are coalitions,
board-seat rules, shareholder agreements, convertible instruments, probabilistic voting, legal
jurisdiction, and time-varying ownership.
