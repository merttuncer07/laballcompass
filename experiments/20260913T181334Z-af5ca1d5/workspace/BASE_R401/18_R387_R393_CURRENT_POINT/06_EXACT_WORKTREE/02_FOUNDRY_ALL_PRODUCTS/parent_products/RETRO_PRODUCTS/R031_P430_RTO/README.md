# Restart Timing Optimizer

RTO is an independent product from **R-031 / P-430**. The source was historically merged into
IM-221, but choosing when to abandon and restart a broad first-passage process is a complete
operations product by itself.

From empirical positive completion times and an explicit restart overhead, RTO computes for each
threshold:

- success probability per attempt;
- expected number of failed attempts;
- expected restart overhead;
- expected total completion time;
- improvement or damage relative to never restarting.

It keeps `NO_RESTART` as a real candidate, so a light-tailed or deterministic process is not forced
through a restart policy.

## Run

```powershell
python -m unittest -v test_rto.py
python demo_heavy_tail_restart.py
```

## Boundary

v0.1 assumes independent identically distributed attempts, fully observed completion samples, and
constant overhead. Next layers are censoring, state-dependent restart cost, partial progress salvage,
parallel attempts, nonstationarity, and online policy updates.
