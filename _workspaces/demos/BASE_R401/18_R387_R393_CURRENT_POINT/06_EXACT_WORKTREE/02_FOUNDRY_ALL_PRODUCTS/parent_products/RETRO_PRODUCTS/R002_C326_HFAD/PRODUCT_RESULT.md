# Product Result — HFAD v0.1

**Retro candidate:** R-002 / C-326 / M-497–M-498  
**Historical decision:** `VARIANT_OF IM-320`  
**Product:** Hodge Flow Attribution Decomposer  
**Status:** independent working product

C-326 did not need a new ontology ID to become a distinct tool. HFAD accepts a discrete oriented
complex and observed edge flow, then returns source-to-sink potential flow, local face circulation,
and global harmonic circulation separately.

In the reproducible filled-triangle/bridge/unfilled-loop network:

- potential flow carried **11.46%** of observed flow energy;
- local face circulation carried **22.14%**;
- global harmonic circulation carried **66.41%**;
- node-balance-only analysis left **48** energy units as one unexplained residual;
- HFAD resolved that residual into **12** local-cycle and **36** global-loop energy units;
- reconstruction residual was exactly zero and structural residuals were below `3e-15`.

Four automated tests pass, including recovery of known components and rejection of an invalid
face-boundary complex. This is an independent product; existing products were not required.

v0.1 uses complete, unweighted finite-complex observations. The next standalone layer is weighted
geometry, noisy/missing edge flow, streaming change detection, and automatic topology construction.

