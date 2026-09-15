# P058 VLRB v0.2 — Verified-Liquidity Redemption Buffer

## Composition
LCM → explicit TRUE_SALE adapter → OFLS. LCM-financed claim face is removed from the liquidatable asset book, proceeds are added to cash, and any face/proceeds discount is written into NAV before OFLS redemption simulation.

## Benchmark result
A verified 40-face claim sold at par produces **40** cash. Baseline redemption needs **41.00698** of forced asset sales and incurs **1.00698** forced-sale cost. After true-sale monetization, forced sale is **0** and forced-sale cost is **0**. With an 80% advance/sale rate, the product explicitly records an **8** discount loss instead of hiding it.

Boundary: borrowing-mode is rejected because OFLS has no liability side. The adapter is valid only when financed claim face is already included in the declared liquidatable asset book and monetization is an actual true sale/removal.

Promotion state: **WORKING_COMPOSITION / BALANCE-SHEET-COMPATIBLE LIQUIDITY BENCHMARK**.
