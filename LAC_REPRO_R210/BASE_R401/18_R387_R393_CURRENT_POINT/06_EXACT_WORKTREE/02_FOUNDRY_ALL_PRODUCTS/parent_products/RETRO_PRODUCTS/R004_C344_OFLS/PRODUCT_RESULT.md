# Product Result — OFLS v0.1

**Retro candidate:** R-004 / C-344 / E-575 + E-576 + E-577  
**Historical decision:** variant of IM-351  
**Product:** Open-Fund Liquidity and Swing-pricing Simulator  
**Status:** independent working product

OFLS closes an open fund's balance sheet through redemption, forced asset sales, swing pricing, and
gating. Swing charge is solved jointly with the sale cost rather than imposed as an unrelated haircut.

In the first 300-unit redemption construction:

- ordinary NAV redemption destroyed **2,086.29** of value and reduced remaining NAV from 100 to **97.02**;
- the first-mover advantage was **6.95 per redeemed unit**;
- full swing pricing charged redeemers **1,815.79**, left zero cost behind, and preserved remaining NAV at 100;
- a 10% gate reduced forced-sale cost to **159.22** while deferring 200 units;
- gate plus full swing left zero externalized cost and made the deferred amount explicit.

Four tests pass. OFLS is a standalone fund-liquidity and policy-design product; current-product
integration is not required.

v0.1 is a one-window deterministic balance-sheet model. The next standalone layer is sequential runs,
asset-sale ordering, stochastic recovery, subscriptions, heterogeneous investors, and endogenous runs.
