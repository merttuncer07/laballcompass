# V2P049 SACAPL — R388 shadow result

**Composition:** `R037 SACPS -> R041 CAPL`

**Non-additive mechanism:** SACPS covariance is inserted into CAPL's quadratic policy-risk objective. The CAPL action cap and turnover feasible set remain unchanged, separating this mechanism from V2P040 BMCAPL.

**Removal control:** identical CAPL action map, constraints, optimizer settings, seed, returns, transaction cost and risk aversion, but with raw sample covariance replacing the support-aware covariance.

**Nearest-family checks:** V2P039 SCCATF (same supplier/different allocation mechanism), V2P040 BMCAPL (same consumer/feasible-set contraction), and V2P034 SCOPG (support geometry used as an identification guard rather than policy-risk geometry).

**Evidence boundary:** deterministic synthetic sparse-support mechanism shell only. No empirical crypto/equity profitability claim.

**Authority:** shadow candidate. It does not change `CURRENT_PRODUCT_AUTHORITY`, Registry455, Products47, or Quality34.
