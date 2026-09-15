# P007 result — VCPA v0.1

Promotion state: **WORKING_COMPOSITION / SYNTHETIC CAPITAL-MARKET BENCHMARK**.

Tests: **5/5 passing**.

Primary benchmark with funding need 100 and capital supply 60:

Without claim verification:

- deployable claim liquidity = **0**;
- residual capital demand = **100**;
- MCPR serves **60**, leaving **40** unserved;
- financing status = **CAPITAL_MARKET_SHORTAGE**.

With compatible verification:

- LCM deployable liquidity = **80**;
- residual capital demand = **20**;
- MCPR clears all 20 at a uniform required return of **10%**;
- VCPA translates 10% into PRIU promised repayment/hurdle terms;
- PRIU finds protected unlocking position **0**;
- financing status = **CAPITAL_CLEARS_AND_PROTECTED_PRIORITY_POSITION_EXISTS**.

Interpretation: verification can affect not only borrowing-base capacity but the existence and marginal price of external capital, which then changes the feasible priority contract.

Scope limit: the MCPR price-to-return interpretation is an explicit adapter contract for this product. Generic MCPR prices must not be assumed to be rates outside that contract.

Evidence label: **synthetic accounting/capital-market benchmark, not real-world financing validation**.
