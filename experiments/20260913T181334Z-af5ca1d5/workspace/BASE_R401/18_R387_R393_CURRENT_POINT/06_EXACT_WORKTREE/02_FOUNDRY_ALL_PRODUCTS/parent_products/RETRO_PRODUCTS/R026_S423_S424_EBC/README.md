# EBC v0.1 — Evidence Borrowing Controller

EBC combines a current normal estimate with historical estimates while controlling two independent
levers:

- `maximum_power` limits how much each historical source may count;
- compatibility weighting reduces borrowing as standardized conflict with current data grows;
- `borrowing_cap_ratio` limits all borrowed precision relative to current precision.

The result exposes every source's conflict score, pre-cap and final power, precision contribution,
the current-information share, and the controlled posterior interval. It can compare current-only,
adaptive borrowing, and uncontrolled pooling.

EBC is a standalone sequential evidence product for repeated tests, markets, factories, or cohorts.
It does not require current-product integration.

Run:

```powershell
python -m unittest -v test_ebc.py
python demo_evidence_borrowing.py
```
