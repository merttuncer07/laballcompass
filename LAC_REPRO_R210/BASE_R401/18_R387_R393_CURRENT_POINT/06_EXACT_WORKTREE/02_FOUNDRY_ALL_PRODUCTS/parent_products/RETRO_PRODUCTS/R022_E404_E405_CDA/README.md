# Channel Dominance Auditor

CDA is an independent product from **R-022 / E-404–E-405**. These records were historically merged
into IM-034, but channel comparison is independently usable even when neither the ontology nor the
underlying theorem is novel.

For two state-by-signal stochastic channels, CDA:

- solves for the best row-stochastic garbling matrix;
- certifies exact Blackwell dominance or equivalence;
- returns the minimum reconstruction error when exact dominance fails;
- identifies incomparable channels that reveal different state partitions;
- evaluates each channel on an explicit prior and action-utility matrix.

## Run

```powershell
python -m unittest -v test_cda.py
python demo_channel_dominance.py
```

## Boundary

v0.1 handles finite known channels and finite actions. Next layers are sampling uncertainty,
confidence regions for dominance, continuous signals, channel cost/privacy/manipulation, and robust
decision value over a class of priors or utilities.
