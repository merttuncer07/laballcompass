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

## September 2026 repair

Channel values now use analytic affine Gaussian upper-envelope integration instead of fixed-node quadrature. `quadrature_points` remains accepted for call compatibility and has no numerical effect. This is the known knowledge-gradient identity, not a new algorithm.

Optional `channel_noise_covariance` with `covariance_channel_names` in exact offered-channel order models a finite joint set of observations. A channel is observed once; replay is idempotent and a deterministic contradiction is rejected. Correlated errors are initially independent of the latent state. The augmented Gaussian is conditioned using square-root projections; singular shared errors are retained without jitter. Without these parameters, every update remains a fresh independent measurement.

Lab CLI: `.venv/bin/python lab.py select-information examples/information-selection/input.json`. See the lab's `examples/information-selection/README.md` and `research/aicc-knowledge-gradient/OBSERVATIONS.md` for exact semantics, numerical limits and upstream references. Current parent tests: 17; three consumers: 19. This verifies numerical behavior, not calibrated real-world utilities or acquisition outcomes.
