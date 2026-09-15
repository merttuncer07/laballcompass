# Contract Safeguard Independence Designer

CSID turns **IM-445 → IM-085** into a working contract/safeguard portfolio engine.

Each failure mode has a probability and consequence. Each safeguard has a cost, coverage by failure
mode, and an evidence family. Controls reading the same evidence family are treated as common-mode:
their coverage is not multiplied as though they were independent. Coverage from genuinely different
evidence families can combine.

The tool enumerates feasible portfolios under a budget and minimizes:

`safeguard cost + expected residual operational loss`.

## Run

```powershell
python -m unittest -v test_csid.py
python demo_contract_design.py
```

## Product boundary

v0.1 is a transparent portfolio engine for explicit failure probabilities and coverage estimates.
It does not infer those inputs from historical data. The next layer is scenario ranges, uncertain
coverage, and an actor-response module that recomputes hidden effort after contract terms change.
