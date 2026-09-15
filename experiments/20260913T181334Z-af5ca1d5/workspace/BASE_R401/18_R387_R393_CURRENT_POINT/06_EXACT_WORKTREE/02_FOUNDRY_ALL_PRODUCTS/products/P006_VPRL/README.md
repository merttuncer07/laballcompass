# P006 — VPRL v0.1

Verified-Claim Priority Relief Ladder.

VPRL keeps the asset and liability sides conceptually separate:

1. LCM measures how much declared asset-side claim value is actually deployable at the requested horizon.
2. That deployable liquidity is applied to a user-declared funding need.
3. PRIU audits only the residual new-money need against the existing liability waterfall.
4. A counterfactual PRIU run on the full funding need quantifies how much priority pressure verification/liquidity conversion relieved.

The product does not treat nominal claims as cash and does not treat verification as profit creation.
