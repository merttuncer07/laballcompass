# Product Result — SCE v0.1

**Retro candidate:** R-029 / S-440  
**Historical decision:** merged into IM-129  
**Product:** Specification Curve Engine  
**Status:** independent working product

SCE executes the full cross-product of user-declared outcome variants, treatment definitions,
control sets, and sample rules. It preserves invalid paths instead of silently dropping them and
summarizes the entire estimate/sign/uncertainty surface.

In the first commercial-effect construction:

- all **8** declared specifications ran successfully;
- every estimate and confidence interval remained positive;
- the estimate nevertheless ranged from **0.5921 to 1.4458**;
- the median estimate was **0.8937**;
- demand adjustment, rather than clipping or sample restriction, explained the large magnitude shift.

Four tests pass, including exact coefficient recovery, complete factorial enumeration, confounding
sensitivity, and visible rank-deficiency handling. SCE is a standalone decision-audit product for
commercial, operational, or scientific effects; it requires no integration with current products.

v0.1 covers linear effects with HC1 standard errors. The next standalone layer is binary/count/time
outcomes, clustered errors, declared interactions, specification grouping, and an interactive report.
