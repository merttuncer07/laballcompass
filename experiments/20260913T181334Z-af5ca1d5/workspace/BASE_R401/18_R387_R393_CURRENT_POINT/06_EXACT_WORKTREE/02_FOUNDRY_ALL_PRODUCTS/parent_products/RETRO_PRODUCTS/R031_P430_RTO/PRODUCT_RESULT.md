# Product Result — RTO v0.1

**Retro candidate:** R-031 / P-430  
**Historical decision:** merged into IM-221  
**Product:** Restart Timing Optimizer  
**Status:** independent working product

RTO chooses whether and when to abandon an attempt from empirical completion times and an explicit
restart overhead. It reports the full attempt accounting and retains never-restart as a candidate.

On independent 120,000-sample training and validation draws from a broad lognormal completion law:

- training selected restart threshold **6.0396**;
- validation no-restart mean completion time was **21.2092**;
- validation restart mean completion time was **11.4751**, a **45.90%** reduction;
- success probability per attempt was **44.43%**;
- expected failed attempts and expected overhead were each **1.2508**;
- a simple median restart achieved 11.5298, slightly worse than the trained threshold.

Four tests pass, including exact two-point accounting and selection of `NO_RESTART` for deterministic
completion. This is an independent operations product.

v0.1 assumes iid attempts, full completion observations, and fixed overhead. The next standalone
layer is censoring, progress salvage, parallel attempts, state-dependent cost, and online drift.

