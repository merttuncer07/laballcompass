from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from carry_engine import fetch_public_carry_data, load_carry_csv, run_carry_backtest, save_carry_csv


SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")


def summarize(results: list[dict]) -> dict:
    rows = []
    for result in results:
        full = result["full_product"]
        removal = result["dtec_removed"]
        always = result["always_on_carry"]
        rows.append(
            {
                "symbol": result["market"]["symbol"],
                "net_return": full["net_return"],
                "maximum_drawdown": full["maximum_drawdown"],
                "annualized_sharpe": full["annualized_sharpe"],
                "dtec_removed_return": removal["net_return"],
                "always_on_return": always["net_return"],
                "dtec_contribution": result["dtec_net_return_contribution"],
                "position_changes": full["position_changes"],
            }
        )
    return {
        "rows": rows,
        "aggregate": {
            "market_count": len(rows),
            "positive_market_count": sum(row["net_return"] > 0 for row in rows),
            "dtec_positive_contribution_count": sum(row["dtec_contribution"] > 0 for row in rows),
            "beats_always_on_count": sum(row["net_return"] > row["always_on_return"] for row in rows),
            "mean_net_return": float(np.mean([row["net_return"] for row in rows])),
            "median_net_return": float(np.median([row["net_return"] for row in rows])),
            "worst_net_return": min(row["net_return"] for row in rows),
            "worst_maximum_drawdown": max(row["maximum_drawdown"] for row in rows),
        },
    }


def render(summary: dict) -> str:
    lines = [
        "# Frozen cross-market funding/basis validation",
        "",
        "| Symbol | Lab net | Max DD | Sharpe | DTEC removed | Always-on | DTEC contribution | Changes |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary["rows"]:
        lines.append(
            f"| {row['symbol']} | {100*row['net_return']:.2f}% | "
            f"{100*row['maximum_drawdown']:.2f}% | {row['annualized_sharpe']:.2f} | "
            f"{100*row['dtec_removed_return']:.2f}% | {100*row['always_on_return']:.2f}% | "
            f"{100*row['dtec_contribution']:.2f} pp | {row['position_changes']} |"
        )
    aggregate = summary["aggregate"]
    lines.extend(
        [
            "",
            f"Positive markets: **{aggregate['positive_market_count']}/{aggregate['market_count']}**.  ",
            f"Positive DTEC contribution: **{aggregate['dtec_positive_contribution_count']}/{aggregate['market_count']}**.  ",
            f"Beat always-on carry: **{aggregate['beats_always_on_count']}/{aggregate['market_count']}**.  ",
            f"Mean/median net: **{100*aggregate['mean_net_return']:.2f}% / {100*aggregate['median_net_return']:.2f}%**.  ",
            f"Worst net / worst drawdown: **{100*aggregate['worst_net_return']:.2f}% / {100*aggregate['worst_maximum_drawdown']:.2f}%**.",
            "",
            "All markets use the same frozen parameters and conservative retail-like two-leg costs. "
            "These are correlated Binance histories, not independent future evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="carry_config.json")
    parser.add_argument("--output-dir", default="carry_validation_output")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for symbol in SYMBOLS:
        csv_path = output / f"{symbol}_carry.csv"
        if not args.offline:
            data = fetch_public_carry_data(symbol, int(config.get("bars", 1500)))
            save_carry_csv(data, csv_path)
        data = load_carry_csv(csv_path, symbol)
        result = run_carry_backtest(data, {**config, "symbol": symbol})
        results.append(result)
        (output / f"{symbol}_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    summary = summarize(results)
    (output / "cross_market_validation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report = render(summary)
    (output / "cross_market_validation.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
