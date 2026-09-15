# Crypto quant mechanism reconstruction

Date: 2026-08-31

## What the "leak" search actually found

I found no credible public dump of a production Jump, Wintermute, GSR or similar crypto strategy that
could responsibly be treated as authentic source code. The best-documented exposed FTX/Alameda code
was not alpha: the CFTC complaint describes a hard-coded auto-liquidation exemption, an "allow
negative" account flag, effectively unbounded credit and faster API routing. It also records the
internal conclusion that insufficient hedging cost Alameda more expected value than all the money it
had made or would make. Those are fraud/risk failures, not mechanisms to reproduce.

Primary source: [CFTC complaint, CFTC v. FTX Trading et al.](https://www.cftc.gov/media/7986/enfftxtradingcomplaint121322/download)

## What professional mechanisms publicly reveal

The consistent mechanism is not a magical next-candle predictor. It is a stack:

1. **Hedgeable fair value.** Price one venue or instrument from another price at which the exposure
   can actually be hedged. Jump explicitly distinguishes passive quoting on a secondary market from
   aggressive trading against a stale quote, with both anchored to an immediate primary-market hedge.
2. **Spread/carry capture.** Earn bid/ask spread, cross-venue dislocation, futures basis or perpetual
   funding while keeping directional exposure small.
3. **Inventory and adverse-flow control.** A quote is widened, reduced or removed when inventory,
   volatility or toxic flow makes the hedge unsafe. The classic reservation-price formulation moves
   quotes against accumulated inventory rather than pretending inventory is free.
4. **Execution is part of alpha.** GSR describes order slicing, multi-venue routing and dynamic
   adjustment to liquidity/volatility. A theoretical signal that cannot survive spread, fees,
   slippage and hedge latency is not an edge.
5. **Book-level risk.** Equal and opposite legs, bounded gross exposure, collateral/venue limits and
   independent kill conditions matter at least as much as prediction.

Sources:

- [Jump Crypto: Dual Flow Batch Auction](https://jumpcrypto.com/resources/dual-flow-batch-auction)
- [GSR: Programmatic Execution](https://www.gsr.io/programmatic-execution)
- [Wintermute: Algorithmic Trading](https://www.wintermute.com/algorithmic-trading)
- [Hummingbot: Cross-Exchange Market Making](https://hummingbot.org/strategies/v1-strategies/cross-exchange-market-making/)
- [Avellaneda and Stoikov: High-frequency trading in a limit order book](https://math.nyu.edu/inmemoriam/avellaneda/HighFrequencyTrading.pdf)

## Why this product starts with funding/basis, not HFT market making

High-frequency market making requires archived order books, queue position, observed fills, maker
rebates, cancel latency and a second executable hedge venue. OHLCV backtests cannot validate it.
Pretending otherwise would create attractive fiction.

Funding/basis carry preserves the important professional structure while remaining measurable with
our current material:

- long spot and short the equal-notional perpetual;
- receive positive funding on the short leg;
- realize basis convergence through spot-minus-perpetual price changes;
- enter only when expected carry can repay both-leg costs and uncertainty;
- leave when the same inequality reverses;
- keep gross, costs and net results separately attributable.

Binance publicly exposes settled funding history and basis/price market data. Research on perpetuals
also supports treating funding as the feedback mechanism linking perpetual and spot prices, while
warning that trading frictions create non-trivial no-arbitrage bands.

Sources:

- [Binance USD-M Futures market-data API](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/24hr-Ticker-Price-Change-Statistics)
- [Bybit funding history API](https://bybit-exchange.github.io/docs/v5/market/history-fund-rate)
- [He, Manela, Ross and von Wachter: Fundamentals of Perpetual Futures](https://arxiv.org/abs/2212.06888)
- [Dai, Li and Yang: Arbitrage in Perpetual Contracts](https://ssrn.com/abstract=5262988)

## Lab reconstruction

| Professional function | Lab material used | Product implementation |
|---|---|---|
| Fair carry estimate | LMDE / ReliabilityTemperedEvidence | Funding persistence + basis convergence + direct carry, weighted by causal forecast error |
| Do not trade noise | DecisionFluctuationGuard | Forecast uncertainty accompanies every expected carry value |
| Survive two-leg costs | V2P033 DTEC | Stateful enter/exit comparison over a 45-event cost-recovery horizon |
| Show where returns went | V2P029 TCEA semantics | Gross return, fees/slippage, net return and removal comparator |
| Directional neutrality | finance mechanism, independently reconstructed | Equal-notional long spot / short perpetual, 1.0x total gross, zero entry delta |

The code was independently written from these public mechanisms and the Lab's own primitives. No
claimed leaked source was copied.

## Evidence produced

With one frozen parameter set and conservative retail-like two-leg costs:

- five full histories: 5/5 positive; mean +1.06%; worst +0.10%; worst drawdown 0.56%;
- 15 chronological windows: 11/15 positive; mean +0.29%; worst -0.23%;
- DTEC marginal contribution: positive in 5/5 markets and 15/15 windows;
- Lab timing versus always-on carry: better in only 7/15 windows.

The robust discovery is **cost-aware persistence**, not proven funding prediction. The raw causal
signal lost money in every full-history market because it switched too often; DTEC converted that
into a slow carry book. The selection layer still needs external venue and forward-paper evidence.

## Next material upgrade

The next version should collect synchronized top-of-book spot and perpetual quotes from two venues,
actual maker/taker schedules, funding caps/interval changes and open interest. That enables a true
executable-edge field:

`expected funding + hedgeable basis convergence - four-way round-trip cost - latency/slippage reserve`

Only after a long shadow ledger reconciles both legs, partial fills and venue failures should an
authenticated executor be considered.
