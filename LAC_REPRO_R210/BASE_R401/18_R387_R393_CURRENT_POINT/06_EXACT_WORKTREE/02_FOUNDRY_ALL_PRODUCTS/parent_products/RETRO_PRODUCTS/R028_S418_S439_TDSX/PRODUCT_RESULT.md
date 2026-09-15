# Product Result — TDSX v0.1

**Retro candidate:** R-028 / S-418 + S-436 + S-437 + S-439  
**Historical decision:** merged into IM-128  
**Product:** Tipping-Distance and Sensitivity-surface Explorer  
**Status:** independent working product

TDSX evaluates a black-box decision metric over declared assumption grids, locates the nearest
decision reversal, and distinguishes joint tipping from one-assumption-at-a-time stress.

In the first two-assumption construction:

- **6,561** surface points were evaluated;
- **92.14%** preserved the baseline decision;
- neither parameter alone tipped the decision inside its declared range;
- together, hidden confounding **1.975** and missing-outcome penalty **0.525** produced the first grid flip;
- an RR=2 confounding E-value was **3.414**;
- the missing-value level needed to tip an example completed mean was **5.0**.

Four tests pass, including honest no-flip reporting. TDSX is a standalone robustness-margin and
assumption-design product; current-product integration is not required.

v0.1 performs finite-grid exploration. The next standalone layer is continuous boundary search,
adaptive meshing, correlated assumption regions, and decision-cost-weighted distance.
