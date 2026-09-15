# OFLS v0.1 — Open-Fund Liquidity and Swing-pricing Simulator

OFLS closes the fund balance sheet through a redemption window. Cash is used first; remaining payout
requires asset sales with linear transaction cost and size-dependent market impact. A gate limits
served units, while swing pricing is solved jointly with the actual sale cost.

The report separates cash paid, deferred units, assets sold, destroyed value, cost borne by redeemers,
cost externalized to remaining holders, first-mover advantage, and remaining NAV dilution. OFLS is a
standalone fund-liquidity policy product; current-product integration is unnecessary.

Run `python -m unittest -v test_ofls.py` and `python demo_redemption_policies.py`.
