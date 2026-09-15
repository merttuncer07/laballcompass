# Product Result — MCPR v0.1

**Retro candidate:** R-011 / C-360 / E-641 + E-642 + E-643  
**Historical decision:** variant of IM-023  
**Product:** Marginal Clearing Price and Rent Calculator  
**Status:** independent working product

MCPR clears divisible offers under merit order, prorates tied marginal blocks, applies a common
clearing price, decomposes payments into offered cost and inframarginal rent, and exposes shortage.

In the first four-generator demand sweep:

- demand 120 cleared at **45**, with payment **5,400** and rent **2,750**;
- demand 121 activated the next offer and raised price to **70**;
- that one-unit demand increase raised payment to **8,470** and rent to **5,750**;
- a demand-200 case served 180, exposed 20 unserved, and applied the declared scarcity price 300;
- equal-price marginal offers were prorated exactly by available quantity.

Four tests pass. MCPR is a standalone auction, procurement, or dispatch scenario product; no current
composition integration is required.

v0.1 assumes divisible single-period offers and fixed demand. The next standalone layer is demand
bids, block/ramp constraints, network congestion, pay-as-bid comparison, and strategic offer sweeps.
