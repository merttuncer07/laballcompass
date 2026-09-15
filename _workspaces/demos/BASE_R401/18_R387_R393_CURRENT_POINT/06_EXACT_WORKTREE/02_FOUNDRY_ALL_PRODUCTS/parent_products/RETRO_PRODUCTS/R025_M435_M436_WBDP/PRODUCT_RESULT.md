# Product Result — WBDP v0.1

**Retro candidate:** R-025 / M-435 + M-436  
**Historical decision:** merged into IM-187  
**Product:** Wasserstein Barycenter and Displacement Planner  
**Status:** independent working product

WBDP computes exact one-dimensional discrete W2 barycenters and displacement paths through joint
quantile segments.

In the first constructions:

- point masses at 0 and 10 moved to a midpoint mass at **5**, with variance **0**;
- an ordinary 50/50 mixture would remain at 0 and 10 with variance **25**;
- the WEST–EAST halfway distribution was exactly **4.9699** Wasserstein units from each endpoint;
- a 35/65 weighted barycenter occupied positions 5.2, 7.8, and 8.5;
- its weighted squared transport objective was **22.477**.

Four tests pass. WBDP is a standalone demand, inventory, geographic allocation, and distribution-risk
planning product; current-product integration is not required.

v0.1 is exact in one dimension. The next standalone layer is multidimensional entropic transport,
capacity constraints, forbidden routes, and time-indexed movement costs.
