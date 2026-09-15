# Adaptive Consequence-Resolution Allocator

ACRA turns **IM-406 → IM-037** into a working measurement-allocation engine. Each decision region
declares time importance, frequency importance, and operational consequence. Each measurement option
declares cost plus time/frequency error. A mixed-integer program selects one resolution per region
under a shared budget to minimize total decision-weighted error.

## Run

```powershell
python -m unittest -v test_acra.py
python demo_resolution_allocation.py
```

## Product boundary

v0.1 allocates among precomputed resolution options. Next layers derive errors from actual window/
sampling operators and adapt allocation online as action margins change.
