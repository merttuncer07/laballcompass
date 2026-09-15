"""Frozen chronological-window validation across multiple crypto markets."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from algotrader import fetch_closed_klines, load_csv, run_research_backtest, save_csv, slice_data


def build_windows(total_bars: int, window_bars: int, step_bars: int) -> list[tuple[int, int]]:
    if window_bars <= 0 or step_bars <= 0 or total_bars < window_bars:
        raise ValueError("invalid chronological window contract")
    windows = [(start, start + window_bars) for start in range(0, total_bars - window_bars + 1, step_bars)]
    final = (total_bars - window_bars, total_bars)
    if windows[-1] != final:
        windows.append(final)
    return windows


def summarize_windows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("At least one window result is required")
    count = len(rows)
    symbols = sorted({str(row["symbol"]) for row in rows})
    return {
        "validation": "FROZEN_CHRONOLOGICAL_WINDOW_LMDE_DTEC_V1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "symbols": symbols,
        "windows": list(rows),
        "aggregate": {
            "window_count": count,
            "positive_window_count": sum(row["net_return"] > 0 for row in rows),
            "dtec_positive_contribution_count": sum(row["dtec_contribution"] > 0 for row in rows),
            "beat_buy_hold_count": sum(row["net_return"] > row["buy_hold_return"] for row in rows),
            "mean_net_return": sum(row["net_return"] for row in rows) / count,
            "median_net_return": sorted(row["net_return"] for row in rows)[count // 2]
            if count % 2
            else sum(sorted(row["net_return"] for row in rows)[count // 2 - 1 : count // 2 + 1]) / 2,
            "worst_net_return": min(row["net_return"] for row in rows),
            "mean_maximum_drawdown": sum(row["maximum_drawdown"] for row in rows) / count,
            "worst_maximum_drawdown": max(row["maximum_drawdown"] for row in rows),
        },
        "protocol": {
            "same_parameters_in_every_window": True,
            "each_window_retrains_only_on_its_own_prefix": True,
            "live_orders": False,
        },
        "boundary": "Historical chronological-window evidence; correlated assets/windows are not independent trials.",
    }


def render_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Frozen chronological-window validation",
        "",
        "Every row uses the same parameters and trains only on that window's prefix.",
        "",
        "| Market | Evaluation start | Evaluation end | Net | Max DD | Buy & hold | DTEC contribution |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in summary["windows"]:
        lines.append(
            f"| {row['symbol']} | {row['start_utc'][:10]} | {row['end_utc'][:10]} | "
            f"{100 * row['net_return']:.2f}% | {100 * row['maximum_drawdown']:.2f}% | "
            f"{100 * row['buy_hold_return']:.2f}% | {100 * row['dtec_contribution']:.2f} pp |"
        )
    aggregate = summary["aggregate"]
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Positive windows: **{aggregate['positive_window_count']}/{aggregate['window_count']}**.",
            f"- DTEC positive contribution: **{aggregate['dtec_positive_contribution_count']}/{aggregate['window_count']}**.",
            f"- Beat buy-and-hold: **{aggregate['beat_buy_hold_count']}/{aggregate['window_count']}**.",
            f"- Mean / median net: **{100 * aggregate['mean_net_return']:.2f}% / {100 * aggregate['median_net_return']:.2f}%**.",
            f"- Worst net: **{100 * aggregate['worst_net_return']:.2f}%**.",
            f"- Mean / worst max DD: **{100 * aggregate['mean_maximum_drawdown']:.2f}% / {100 * aggregate['worst_maximum_drawdown']:.2f}%**.",
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
    parser = argparse.ArgumentParser(description="Run frozen chronological-window validation")
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    parser.add_argument("--history-bars", type=int, default=10000)
    parser.add_argument("--window-bars", type=int, default=3500)
    parser.add_argument("--step-bars", type=int, default=2000)
    parser.add_argument("--output-dir", type=Path, default=Path("time_validation_output"))
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    base_config = json.loads(args.config.read_text(encoding="utf-8"))
    if args.window_bars <= int(base_config["train_bars"]) + int(base_config["refit_bars"]):
        raise ValueError("window must exceed train_bars + refit_bars")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    windows = build_windows(args.history_bars, args.window_bars, args.step_bars)
    rows = []
    for raw_symbol in args.symbols:
        symbol = raw_symbol.upper()
        full_path = args.output_dir / f"{symbol}_{base_config['interval']}_{args.history_bars}.csv"
        if args.offline:
            full_data = load_csv(full_path)
        else:
            full_data = fetch_closed_klines(
                symbol, base_config["interval"], args.history_bars
            )
            save_csv(full_data, full_path)
            full_data = load_csv(full_path)
        config = dict(base_config)
        config["symbol"] = symbol
        config["bars"] = args.window_bars
        for index, (start, stop) in enumerate(windows, start=1):
            result = run_research_backtest(slice_data(full_data, start, stop), config)
            full = result["full_product"]
            row = {
                "symbol": symbol,
                "window": index,
                "source_rows": [start, stop],
                "start_utc": full["start_utc"],
                "end_utc": full["end_utc"],
                "net_return": full["net_return"],
                "maximum_drawdown": full["maximum_drawdown"],
                "buy_hold_return": full["buy_hold_return"],
                "dtec_removed_net_return": result["dtec_removal"]["net_return"],
                "dtec_contribution": result["dtec_net_return_contribution"],
                "position_changes": full["position_changes"],
            }
            rows.append(row)
            print(
                f"{symbol} window {index}/{len(windows)}: net={100 * row['net_return']:.2f}%, "
                f"DTEC={100 * row['dtec_contribution']:.2f} pp"
            )
    summary = summarize_windows(rows)
    (args.output_dir / "chronological_validation.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (args.output_dir / "chronological_validation.md").write_text(
        render_markdown(summary), encoding="utf-8"
    )
    print(f"Wrote {len(rows)} chronological window results to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
