# Lab Crypto Algotrader — BTCUSDT 1h

## Frozen walk-forward result

| Metric | Full Lab product | DTEC removed |
|---|---:|---:|
| Net return | 15.23% | -10.69% |
| Maximum drawdown | 6.85% | 16.44% |
| Annualized Sharpe | 3.046 | -4.417 |
| Position changes | 39 | 697 |
| Cost drag | 3.14% | 13.24% |

Buy-and-hold return over the evaluated path: **23.33%**.  
DTEC contribution on this sample: **25.92 percentage points**.  
Latest paper target exposure: **59.2%**.

## Interpretation

The full product is LMDE → DTEC with causal next-open execution, volatility sizing, transaction costs and a drawdown cooldown. DTEC is also removed and rerun on the same sample; a negative contribution means the full composition is not supported there.

## Boundary

Historical paper evidence only. No future return or live-profit claim.
The program never submits an exchange order.
