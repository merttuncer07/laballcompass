# P007 — VCPA v0.1

Verified-Claim Capital Priority Auction.

Directed composition:

1. LCM converts eligible verified asset-side claims into deployable liquidity.
2. Residual funding need becomes MCPR capital demand.
3. MCPR `Offer.price` is accepted only under an explicit VCPA adapter contract: it is a non-negative one-period simple required return rate.
4. The uniform marginal clearing rate determines both promised repayment and lender hurdle in PRIU.
5. PRIU then tests which priority positions make the market-cleared financing recoverable and whether existing claims remain protected.

This prevents a generic market price from being silently reinterpreted as a financing rate.
