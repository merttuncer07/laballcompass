# Trigger Policy Designer

This is a CSV-facing productization of the Lab's `IM455_IM094_DTTC` trigger-channel parent. It
chooses a signal and threshold using the earlier part of a dataset, then reports performance on the
later holdout part.

The objective prices:

- missed protected events;
- unnecessary triggers;
- verification work per trigger;
- declared manipulation exposure of the signal.

Both high-value and low-value trigger directions are supported. The report compares candidates and
the selected policy against always-trigger and never-trigger baselines.

## Run

```powershell
python trigger_designer.py example_config.json example_machine_history.csv --output example_output.json --report example_report.md
python -m unittest -v test_trigger_designer.py
```

## Important boundary

CSV order is treated as chronological. The threshold is selected only on the first partition and
evaluated on the later partition. That is more honest than an in-sample score but is not proof of
future stability or causal benefit. Costs must be expressed in a common unit, and the event label
must represent the operational loss that the trigger is intended to prevent.

## Change from the parent

The native DTTC parent optimizes a threshold and candidate over supplied arrays. This shell keeps
the consequence-targeted objective while adding ordinary CSV input, low-direction triggers,
per-trigger verification cost, chronological holdout evaluation, always/never comparators, warnings
and saved operational reports. It does not change the canonical parent.
