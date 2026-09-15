from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

from carry_engine import load_carry_csv, run_carry_backtest, slice_carry_data
from validate_carry_markets import SYMBOLS


def build_windows(length: int, width: int = 600, step: int = 450) -> list[tuple[int, int]]:
    if length < width:
        raise ValueError("history shorter than validation window")
    starts = list(range(0, length - width + 1, step))
    tail = length - width
    if starts[-1] != tail:
        starts.append(tail)
    return [(start, start + width) for start in starts]


def summarize(rows: list[dict]) -> dict:
    return {
        "rows": rows,
        "aggregate": {
            "window_count": len(rows),
            "positive_window_count": sum(row["net_return"] > 0 for row in rows),
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
        "# Chronological funding/basis validation",
        "",
        "| Symbol | Evaluation period | Lab net | Max DD | DTEC removed | Always-on | DTEC contribution |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary["rows"]:
        lines.append(
            f"| {row['symbol']} | {row['start_utc'][:10]} to {row['end_utc'][:10]} | "
            f"{100*row['net_return']:.2f}% | {100*row['maximum_drawdown']:.2f}% | "
            f"{100*row['dtec_removed_return']:.2f}% | {100*row['always_on_return']:.2f}% | "
            f"{100*row['dtec_contribution']:.2f} pp |"
        )
    aggregate = summary["aggregate"]
    lines.extend(
        [
            "",
            f"Positive windows: **{aggregate['positive_window_count']}/{aggregate['window_count']}**.  ",
            f"Positive DTEC contribution: **{aggregate['dtec_positive_contribution_count']}/{aggregate['window_count']}**.  ",
            f"Beat always-on carry: **{aggregate['beats_always_on_count']}/{aggregate['window_count']}**.  ",
            f"Mean/median net: **{100*aggregate['mean_net_return']:.2f}% / {100*aggregate['median_net_return']:.2f}%**.  ",
            f"Worst net / worst drawdown: **{100*aggregate['worst_net_return']:.2f}% / {100*aggregate['worst_maximum_drawdown']:.2f}%**.",
            "",
            "Each window rebuilds its forecast from its own prefix. Windows overlap, so the count is diagnostic rather than an independent-trial claim.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="carry_config.json")
    parser.add_argument("--data-dir", default="carry_validation_output")
    parser.add_argument("--output-dir", default="carry_time_validation_output")
    parser.add_argument("--window", type=int, default=600)
    parser.add_argument("--step", type=int, default=450)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    rows = []
    for symbol in SYMBOLS:
        data = load_carry_csv(Path(args.data_dir) / f"{symbol}_carry.csv", symbol)
        for window_index, (start, stop) in enumerate(build_windows(len(data), args.window, args.step), 1):
            window = slice_carry_data(data, start, stop)
            result = run_carry_backtest(window, {**config, "symbol": symbol})
            full = result["full_product"]
            rows.append(
                {
                    "symbol": symbol,
                    "window": window_index,
                    "start_utc": datetime.fromtimestamp(
                        window.timestamp_ms[int(config["min_history"])] / 1000, tz=timezone.utc
                    ).isoformat(),
                    "end_utc": datetime.fromtimestamp(window.timestamp_ms[-1] / 1000, tz=timezone.utc).isoformat(),
                    "net_return": full["net_return"],
                    "maximum_drawdown": full["maximum_drawdown"],
                    "dtec_removed_return": result["dtec_removed"]["net_return"],
                    "always_on_return": result["always_on_carry"]["net_return"],
                    "dtec_contribution": result["dtec_net_return_contribution"],
                }
            )
    summary = summarize(rows)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "chronological_validation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report = render(summary)
    (output / "chronological_validation.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
