# Overlap-aware Weight Stabilizer

OWS turns **IM-274 → IM-290** into a working support audit and controlled reweighting engine.

It reports effective sample size, maximum normalized weight, and top-one-percent weight mass before
estimating anything. It then chooses a clipping cap by minimizing a transparent proxy:

`bias_aversion × worst-case bounded-outcome clipping bias² + weighted variance`.

The hard bias bound is always reported. `bias_aversion` is an explicit operational tradeoff, so the
tool does not hide a variance-reducing bias choice inside an automatic default.

The result keeps the raw exact-weight estimate, stabilized estimate, selected cap, ESS change, and
support status separately visible.

## Run

```powershell
python -m unittest -v test_ows.py
python demo_weight_stabilization.py
```

## Product boundary

v0.1 assumes supplied non-negative importance weights and bounded outcomes. It does not manufacture
support where none exists; low ESS is reported as `SUPPORT_FRAGILE`. Next layers estimate density
ratios with cross-fitting and return partial-identification bounds in unsupported regions.
