# Decision-Relevant Explorer

DRE turns **IM-334 → IM-094** into a working sequential exploration policy. It values a measurement
only when the uncertain option can cross the current action boundary, the new observation will
materially reduce that uncertainty, and enough future decisions remain to benefit.

Its score combines immediate expected payoff with a Gaussian decision-crossing value, posterior
uncertainty reduction, remaining horizon, and measurement cost. A far-below option is not explored
merely because its variance is large.

## Run

```powershell
python -m unittest -v test_dre.py
python demo_decision_exploration.py
```

## Product boundary

v0.1 uses independent Gaussian arm posteriors and known observation noise. Next layers are correlated
actions, context/state, non-Gaussian outcomes, and action-dependent information channels.
