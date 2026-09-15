# Target-Weighted Model Reducer

TWMR turns **IM-178 → IM-326** into a working target-specific state-reduction engine. Under a state
dimension budget it enumerates candidate retained-state subsets and minimizes error in the complete
past-input to protected-future-output impulse-response sequence.

It also reports a state-energy baseline, making it visible when a large controllable state carries
little information to the actual protected output.

## Run

```powershell
python -m unittest -v test_twmr.py
python demo_target_model_reduction.py
```

## Product boundary

v0.1 performs coordinate-subset reduction for small linear discrete-time systems. Next layers are
continuous projection bases, stability/error certificates, larger-system search, and several
protected outputs with explicit consequence weights.
