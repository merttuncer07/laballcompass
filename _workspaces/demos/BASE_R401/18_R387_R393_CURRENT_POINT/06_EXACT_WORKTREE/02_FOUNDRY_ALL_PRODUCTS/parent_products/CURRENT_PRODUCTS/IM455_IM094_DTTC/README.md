# Decision-Targeted Trigger Channel Designer

DTTC turns **IM-455 → IM-094** into a working trigger-design engine. It selects both a signal channel
and an activation threshold by minimizing declared operational loss:

`FN cost × P(FN) + FP cost × P(FP) + verification cost + manipulation cost`.

The input is a common scenario field containing the protected loss/event and candidate trigger
signals. The output is a ranked trigger policy. Correlation is reported as a diagnostic but does not
control the choice unless the operational objective makes it relevant.

## Run

```powershell
python -m unittest -v test_dttc.py
python demo_trigger_design.py
```

## Product boundary

v0.1 supports one binary protected action, scalar trigger channels, fixed candidate costs, and
quantile threshold search. The next layer is train/deployment separation, spatial/temporal basis-risk
terms, budget constraints, and actor responses that change when the published policy changes.
