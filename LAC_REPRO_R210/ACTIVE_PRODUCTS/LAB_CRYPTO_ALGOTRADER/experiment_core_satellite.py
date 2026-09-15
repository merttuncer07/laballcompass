"""Test the native V2P031 CSAE composition against the frozen base product."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from algotrader import _path_metrics, build_path, load_csv, slice_data
from validate_time_windows import build_windows


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LMDE -> CSAE -> DTEC removal experiment")
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    parser.add_argument("--history-bars", type=int, default=10000)
    parser.add_argument("--window-bars", type=int, default=3500)
    parser.add_argument("--step-bars", type=int, default=2000)
    parser.add_argument("--data-dir", type=Path, default=Path("time_validation_output"))
    parser.add_argument("--output", type=Path, default=Path("experiments/core_satellite_result.json"))
    args = parser.parse_args(argv)
    base_config = json.loads(args.config.read_text(encoding="utf-8"))
    windows = build_windows(args.history_bars, args.window_bars, args.step_bars)
    rows: list[dict[str, Any]] = []
    for raw_symbol in args.symbols:
        symbol = raw_symbol.upper()
        data = load_csv(args.data_dir / f"{symbol}_{base_config['interval']}_{args.history_bars}.csv")
        config = dict(base_config)
        config.update(
            {
                "symbol": symbol,
                "bars": args.window_bars,
                "core_fast_window": 64,
                "core_slow_window": 256,
                "core_position": 1.0,
            }
        )
        for index, (start, stop) in enumerate(windows, start=1):
            window = slice_data(data, start, stop)
            base_path, _ = build_path(window, config, use_dtec=True, use_core_satellite=False)
            candidate_path, details = build_path(
                window, config, use_dtec=True, use_core_satellite=True
            )
            base = _path_metrics(window, config, base_path)
            candidate = _path_metrics(window, config, candidate_path)
            row = {
                "symbol": symbol,
                "window": index,
                "base_net_return": base["net_return"],
                "candidate_net_return": candidate["net_return"],
                "candidate_minus_base": candidate["net_return"] - base["net_return"],
                "base_maximum_drawdown": base["maximum_drawdown"],
                "candidate_maximum_drawdown": candidate["maximum_drawdown"],
                "base_position_changes": base["position_changes"],
                "candidate_position_changes": candidate["position_changes"],
                "core_active_fraction": details["core_satellite"]["core_active_fraction"],
            }
            rows.append(row)
            print(
                f"{symbol} W{index}: base={100 * base['net_return']:.2f}%, "
                f"CSAE={100 * candidate['net_return']:.2f}%, "
                f"delta={100 * row['candidate_minus_base']:.2f} pp"
            )
    count = len(rows)
    payload = {
        "experiment": "NATIVE_V2P031_CSAE_ADDITION_TO_LMDE_DTEC",
        "candidate": "LMDE -> CSAE(64,256,core=1.0) -> DTEC",
        "comparator": "LMDE -> DTEC",
        "parameters_inherited_from_native_parent": True,
        "rows": rows,
        "aggregate": {
            "windows": count,
            "candidate_wins": sum(row["candidate_minus_base"] > 0 for row in rows),
            "mean_delta": sum(row["candidate_minus_base"] for row in rows) / count,
            "worst_delta": min(row["candidate_minus_base"] for row in rows),
            "candidate_positive_windows": sum(row["candidate_net_return"] > 0 for row in rows),
            "candidate_mean_return": sum(row["candidate_net_return"] for row in rows) / count,
            "candidate_worst_return": min(row["candidate_net_return"] for row in rows),
            "candidate_mean_drawdown": sum(row["candidate_maximum_drawdown"] for row in rows) / count,
            "candidate_worst_drawdown": max(row["candidate_maximum_drawdown"] for row in rows),
        },
        "decision": "PENDING",
    }
    aggregate = payload["aggregate"]
    # This classification records the result; it does not gate unrelated Lab work.
    payload["decision"] = (
        "RETAIN_FOR_FURTHER_VALIDATION"
        if aggregate["candidate_wins"] >= 10
        and aggregate["mean_delta"] > 0
        and aggregate["candidate_worst_drawdown"] <= 0.18
        else "REJECT_FROM_PRODUCT"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Decision: {payload['decision']}; wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
