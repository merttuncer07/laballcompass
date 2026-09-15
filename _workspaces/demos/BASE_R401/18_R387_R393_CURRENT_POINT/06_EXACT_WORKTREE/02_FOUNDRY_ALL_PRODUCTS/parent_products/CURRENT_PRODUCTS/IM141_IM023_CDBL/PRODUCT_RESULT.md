# Product Result — CDBL v0.1

**Composition:** IM-141 → IM-023  
**Product:** Connected Deployable Bottleneck Locator  
**Status:** working reference product

CDBL distinguishes nominal inventory, active inventory, and material that can actually reach a
target through capacity-, conversion-, and deadline-constrained paths. It locates the current
rate-limiting layer by adding an equal capacity increment to every edge and active-stock location
and measuring marginal delivered gain after re-optimization.

In the reproducible six-node deployment network:

- **1,500** nominal units became **830** active units;
- only **176.4** units reached the target by the five-step deadline, **11.76%** of nominal stock;
- a nominally connected warehouse path arriving too late carried zero useful flow;
- adding 20 units to `processor_to_site` increased delivery by **19.6** units;
- the same increment at every other current edge or stock location produced zero gain, identifying
  the current bottleneck without being distracted by stranded inventory.

Three unit tests pass, including the no-in-horizon-path boundary case that was discovered and fixed
during construction.

v0.1 handles one divisible material with deterministic capacity, yield, and lead time. The live
extension path is multi-commodity compatibility, dated demand, stochastic disruption, shared
capacities, integer activation, and intervention cost.
