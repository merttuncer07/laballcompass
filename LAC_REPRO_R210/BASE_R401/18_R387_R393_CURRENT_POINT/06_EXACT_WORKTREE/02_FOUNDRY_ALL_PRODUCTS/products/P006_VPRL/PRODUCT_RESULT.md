# P006 result — VPRL v0.1

Promotion state: **WORKING_COMPOSITION / SYNTHETIC ACCOUNTING BENCHMARK**.

Tests: **5/5 passing**.

Primary benchmark:

- declared funding need = **100**;
- unverified nominal receivable = **100**, deployable liquidity = **0**;
- after compatible verification, LCM deployable liquidity = **80**;
- residual new-money need falls **100 -> 20**;
- liquidity coverage fraction = **80%**.

Priority consequence in the benchmark:

- financing the full 100 requires a priority arrangement for which no unlocking position also protects all existing claims;
- after verified-liquidity conversion reduces new money to 20, PRIU finds a protected unlocking position at position **0**;
- VPRL therefore records `priority_protection_improved = true`.

Interpretation: verification can have value beyond a higher borrowing base. By shrinking the residual financing need, it can change whether a priority reset can be made financeable without modeled harm to existing claims.

Scope limit: LCM contains no funding-price model, so VPRL does **not** claim the 80 units are costless. Financing price is deliberately left to a separate capital-supply interface.

Evidence label: **synthetic accounting benchmark; no real-world credit calibration**.
