# Product Result — CBAC v0.1

**Retro candidate:** R-050 / M-583 + M-585 + S-744 + S-745  
**Historical decision:** positive-control / known transfer  
**Product:** Covariate-Balanced Assignment Certificate  
**Status:** independent working product

CBAC creates fixed-size randomized assignments, defines a covariance-aware balance acceptance region,
and samples randomly within it instead of replacing randomization with one deterministic optimum.

In the first 80-person, five-covariate construction:

- arm sizes were exactly **40/40**;
- **8,000** random assignments were generated and the best-balanced **1%** formed an 80-assignment pool;
- the selected assignment lay at distance percentile **0.825%**;
- Mahalanobis imbalance fell **86.0%** relative to the first random draw;
- maximum absolute standardized mean difference was **0.1242**;
- constant covariates are explicitly reported and ignored safely.

Four tests pass. CBAC is a standalone experiment, rollout, and allocation-design product; current
product integration is not required.

v0.1 handles complete pretreatment covariates and two fixed-size arms. The next standalone layer is
blocks, multiple arms, missing covariates, sequential arrivals, cluster assignment, and randomization
inference.
