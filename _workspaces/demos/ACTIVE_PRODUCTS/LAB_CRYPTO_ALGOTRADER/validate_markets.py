"""Frozen cross-market validation for the Lab Crypto Algotrader."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from algotrader import fetch_closed_klines, load_csv, run_research_backtest, save_csv


DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")


def summarize(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not results:
        raise ValueError("At least one market result is required")
    rows = []
    for result in results:
        full = result["full_product"]
        removal = result["dtec_removal"]
        rows.append(
            {
                "symbol": result["market"]["symbol"],
                "interval": result["market"]["interval"],
                "net_return": full["net_return"],
                "maximum_drawdown": full["maximum_drawdown"],
                "buy_hold_return": full["buy_hold_return"],
                "dtec_removed_net_return": removal["net_return"],
                "dtec_contribution": result["dtec_net_return_contribution"],
                "position_changes": full["position_changes"],
                "cost_drag": full["cost_drag"],
                "latest_paper_exposure": result["paper_signal"]["target_spot_exposure"],
                "data_sha256": result["data"]["sha256"],
            }
        )
    count = len(rows)
    return {
        "validation": "FROZEN_CROSS_MARKET_LMDE_DTEC_V1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "markets": rows,
        "aggregate": {
            "market_count": count,
            "positive_market_count": sum(row["net_return"] > 0 for row in rows),
            "dtec_positive_contribution_count": sum(row["dtec_contribution"] > 0 for row in rows),
            "beat_buy_hold_count": sum(
                row["net_return"] > row["buy_hold_return"] for row in rows
            ),
            "mean_net_return": sum(row["net_return"] for row in rows) / count,
            "worst_net_return": min(row["net_return"] for row in rows),
            "mean_maximum_drawdown": sum(row["maximum_drawdown"] for row in rows) / count,
            "worst_maximum_drawdown": max(row["maximum_drawdown"] for row in rows),
            "mean_dtec_contribution": sum(row["dtec_contribution"] for row in rows) / count,
        },
        "protocol": {
            "same_parameters_across_markets": True,
            "symbol_is_the_only_config_change": True,
            "live_orders": False,
        },
        "boundary": "Cross-market historical paper validation, not a future-profit claim.",
    }


def render_markdown(summary: Mapping[str, Any]) -> str:
    aggregate = summary["aggregate"]
    lines = [
        "# Frozen cross-market validation",
        "",
        "The same configuration was used for every market; only the symbol changed.",
        "",
        "| Market | Net | Max DD | Buy & hold | DTEC removed | DTEC contribution | Changes |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary["markets"]:
        lines.append(
            f"| {row['symbol']} {row['interval']} | {100 * row['net_return']:.2f}% | "
            f"{100 * row['maximum_drawdown']:.2f}% | {100 * row['buy_hold_return']:.2f}% | "
            f"{100 * row['dtec_removed_net_return']:.2f}% | "
            f"{100 * row['dtec_contribution']:.2f} pp | {row['position_changes']} |"
        )
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Positive markets: **{aggregate['positive_market_count']}/{aggregate['market_count']}**.",
            f"- DTEC positive contribution: **{aggregate['dtec_positive_contribution_count']}/{aggregate['market_count']}**.",
            f"- Beat buy-and-hold: **{aggregate['beat_buy_hold_count']}/{aggregate['market_count']}**.",
            f"- Mean net return: **{100 * aggregate['mean_net_return']:.2f}%**.",
            f"- Worst net return: **{100 * aggregate['worst_net_return']:.2f}%**.",
            f"- Mean maximum drawdown: **{100 * aggregate['mean_maximum_drawdown']:.2f}%**.",
            f"- Worst maximum drawdown: **{100 * aggregate['worst_maximum_drawdown']:.2f}%**.",
            "",
            "## Boundary",
            "",
            summary["boundary"],
            "No exchange order was submitted.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run frozen cross-market validation")
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS))
    parser.add_argument("--output-dir", type=Path, default=Path("validation_output"))
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    base_config = json.loads(args.config.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for raw_symbol in args.symbols:
        symbol = raw_symbol.upper()
        config = dict(base_config)
        config["symbol"] = symbol
        data_path = args.output_dir / f"{symbol}_{config['interval']}.csv"
        if args.offline:
            data = load_csv(data_path)
        else:
            data = fetch_closed_klines(symbol, config["interval"], int(config["bars"]))
            save_csv(data, data_path)
            data = load_csv(data_path)
        result = run_research_backtest(data, config)
        results.append(result)
        (args.output_dir / f"{symbol}_result.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
        print(
            f"{symbol}: net={100 * result['full_product']['net_return']:.2f}%, "
            f"DTEC contribution={100 * result['dtec_net_return_contribution']:.2f} pp"
        )
    summary = summarize(results)
    (args.output_dir / "cross_market_validation.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (args.output_dir / "cross_market_validation.md").write_text(
        render_markdown(summary), encoding="utf-8"
    )
    print(f"Wrote frozen validation for {len(results)} markets to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
