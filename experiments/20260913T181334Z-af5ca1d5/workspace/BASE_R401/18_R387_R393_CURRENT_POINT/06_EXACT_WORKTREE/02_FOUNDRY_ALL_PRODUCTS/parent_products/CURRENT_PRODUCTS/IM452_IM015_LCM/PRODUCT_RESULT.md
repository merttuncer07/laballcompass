# IM-452 → IM-015 product result: Liquidity Conversion Map v0.1

LCM is an executable allocation engine that prevents nominal claims from being counted as immediately
usable liquidity. It maps each claim through verification, financing eligibility, channel capacity,
advance rate, time horizon, and anchor-concentration constraints.

## Construction result

The first portfolio contained five receivable/inventory claims and three funding channels.

| State | Amount |
|---|---:|
| Nominal claims | 1,080,000.00 |
| Verified within current horizon | 900,000.00 |
| Financeable face | 900,000.00 |
| Optimally deployable liquidity | **588,970.59** |

The gap is produced by advance rates, lender capacities, claim eligibility, and anchor concentration;
it is not accounting disappearance.

Independently verifying the previously unverified C4 receivable increased optimized deployable
liquidity from 588,970.59 to 700,000.00. The measured marginal value of that verification was
**111,029.41**.

## Working software

- explicit nominal/verified/financeable/deployable state ledger;
- verifier and claim-type eligibility;
- time-to-verification horizon;
- lender liquidity capacities and advance rates;
- anchor concentration limits;
- optimal cross-channel allocation through linear programming;
- marginal verification-value calculation;
- three automated tests, all passing.

## Next construction layer

Add document discrepancy/failure probabilities, recourse and credit risk, financing cost, and dated
cash requirements. This will let the tool choose not just maximum liquidity, but the cheapest robust
verification-and-funding path for a required payment schedule.
