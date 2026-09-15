# Lab Crypto Algotrader

The primary research line is now a **market-neutral spot/perpetual funding-basis engine**. The older
spot long/cash engine remains available as a directional satellite, but its 15 chronological windows
showed regime dependence and it is not the product core.

## Market-neutral carry engine

The engine holds equal-notional long spot and short USDT perpetual legs only when a causal
funding-plus-basis forecast can repay the two-leg transition cost under Lab uncertainty control.
It uses public settled funding records and public spot prices, charges retail-like fees/slippage,
closes the paper position at the sample end and contains no authenticated order endpoint.

```powershell
python carry_cli.py --config carry_config.json --output-dir carry_output
```

Reproduce from the frozen CSV:

```powershell
python carry_cli.py --config carry_config.json --data carry_output/BTCUSDT_carry.csv --output-dir carry_output
```

Cross-market and chronological checks:

```powershell
python validate_carry_markets.py --config carry_config.json --output-dir carry_validation_output
python validate_carry_time_windows.py --config carry_config.json --data-dir carry_validation_output --output-dir carry_time_validation_output
```

Frozen results at 2026-08-31:

- full-history market net was positive in 5/5 symbols; mean +1.06%, worst +0.10%;
- DTEC contributed positively in 5/5 symbols;
- 11/15 chronological windows were positive; mean +0.29%, worst -0.23%;
- DTEC contributed positively in 15/15 windows, chiefly by preventing cost-destructive churn;
- the Lab selector beat always-on carry in only 7/15 windows, so selection alpha is not established.

See `QUANT_MECHANISM_RECONSTRUCTION.md` for the public-source mechanism reconstruction and
`carry_time_validation_output/chronological_validation.md` for the least flattering complete result.

## Directional satellite

A Lab-produced, paper-first Binance Spot long/cash algotrader. It is an independent product runtime:
it does not import the Lab repository after extraction.

The frozen strategy is `LMDE → DTEC` plus causal next-open execution, volatility sizing, transaction
costs and a drawdown cooldown. Every run also removes DTEC and reruns the same history so its marginal
contribution is visible.

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run with fresh public market data

```powershell
python cli.py run --config config.json --output-dir output
```

This downloads only closed public Binance spot candles. It writes:

- `latest_backtest.json`;
- `latest_report.md`;
- `paper_signal.json`;
- append-only `paper_ledger.jsonl`;
- the frozen candle CSV used by the run.

Reproduce without downloading again:

```powershell
python cli.py run --config config.json --data output/BTCUSDT_1h.csv --offline --output-dir output_offline
```

Run tests:

```powershell
python -m unittest -v test_algotrader.py test_carry_engine.py
```

Run the same frozen configuration across five markets:

```powershell
python validate_markets.py --config config.json --output-dir validation_output
```

This changes only the symbol and writes every per-market result plus an aggregate report. Negative
markets are retained in the summary.

Run longer chronological-window validation:

```powershell
python validate_time_windows.py --config config.json --output-dir time_validation_output
```

The default downloads 10,000 hourly candles for BTC, ETH and SOL and evaluates the frozen product in
multiple 3,500-bar windows. Each window trains only on its own prefix.

## Safety boundary

- The carry engine is delta-neutral at entry but is not risk-free: basis, venue, collateral,
  liquidation/ADL, fill and operational risk remain.
- Its historical backtest uses mark/open proxies and fixed costs, not executable archived books.
- The directional satellite is spot long/cash only. The carry engine uses a fully collateralized
  paper perpetual short, capped at 0.5 notional per unit equity and no borrowed leverage.
- Fees and slippage are charged on every fractional position change.
- Signals execute on the next candle open in the backtest.
- The loss that triggers a drawdown cooldown is never erased.
- The program contains no authenticated exchange client and sends zero orders.
- Historical or paper profitability is not evidence of future profitability.

Live execution is a separate future product stage requiring a sufficiently long paper ledger,
exchange-filter handling, reconciliation, idempotent orders, kill switches and explicit authorization.
