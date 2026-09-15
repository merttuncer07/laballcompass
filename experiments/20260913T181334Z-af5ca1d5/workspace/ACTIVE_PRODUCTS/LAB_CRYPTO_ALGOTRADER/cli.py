from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from algotrader import (
    fetch_closed_klines,
    load_csv,
    render_report,
    run_research_backtest,
    save_csv,
    save_paper_signal,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lab-native paper-first crypto algotrader")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Download closed public spot candles")
    fetch_parser.add_argument("--symbol", default="BTCUSDT")
    fetch_parser.add_argument("--interval", default="1h")
    fetch_parser.add_argument("--bars", type=int, default=3000)
    fetch_parser.add_argument("--output", type=Path, required=True)

    run_parser = subparsers.add_parser("run", help="Backtest and write the latest paper signal")
    run_parser.add_argument("--config", type=Path, default=Path("config.json"))
    run_parser.add_argument("--data", type=Path)
    run_parser.add_argument("--offline", action="store_true")
    run_parser.add_argument("--output-dir", type=Path, default=Path("output"))

    args = parser.parse_args(argv)
    if args.command == "fetch":
        data = fetch_closed_klines(args.symbol, args.interval, args.bars)
        save_csv(data, args.output)
        print(f"Wrote {len(data)} closed candles to {args.output}")
        return 0

    config = json.loads(args.config.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cache = args.data or args.output_dir / f"{config['symbol']}_{config['interval']}.csv"
    if args.offline:
        data = load_csv(cache)
    else:
        data = fetch_closed_klines(config["symbol"], config["interval"], int(config["bars"]))
        save_csv(data, cache)
        data = load_csv(cache)
    result = run_research_backtest(data, config)
    result_path = args.output_dir / "latest_backtest.json"
    report_path = args.output_dir / "latest_report.md"
    signal_path = args.output_dir / "paper_signal.json"
    ledger_path = args.output_dir / "paper_ledger.jsonl"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    report_path.write_text(render_report(result), encoding="utf-8")
    signal = save_paper_signal(result, signal_path, ledger_path)
    print(
        f"Wrote {result_path}, {report_path}, and {signal_path}; "
        f"net={100 * result['full_product']['net_return']:.2f}%, "
        f"paper_exposure={100 * signal['target_spot_exposure']:.1f}%, orders_sent=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
