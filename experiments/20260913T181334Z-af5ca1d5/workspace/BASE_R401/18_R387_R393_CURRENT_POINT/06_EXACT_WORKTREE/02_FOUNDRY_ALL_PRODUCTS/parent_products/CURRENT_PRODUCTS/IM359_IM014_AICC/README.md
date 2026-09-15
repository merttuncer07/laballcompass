# Adaptive Information-Channel Controller

AICC turns **IM-359 → IM-014** into a working information controller. Given the current Gaussian
belief, available measurement channels, channel noise/cost, and downstream discrete actions, it
computes each channel's expected value from the action changes that its possible observations can
induce. It then measures through the best positive-value channel and updates the belief.

The policy adapts as uncertainty and the current action boundary change. A cheap precise channel
that measures a high-variance nuisance receives zero decision value.

## Run

```powershell
python -m unittest -v test_aicc.py
python demo_adaptive_channels.py
```

## Product boundary

v0.1 assumes shared sender/receiver action value, Gaussian linear channels, and a finite offered
channel set. Next layers are strategic objective mismatch, endogenous/garbled signal design,
non-Gaussian beliefs, repeated-agent response, and disclosure constraints.
