from __future__ import annotations

import argparse
import json
from pathlib import Path

from carry_engine import (
    fetch_public_carry_data,
    load_carry_csv,
    render_carry_report,
    run_carry_backtest,
    save_carry_paper_signal,
    save_carry_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Paper-only spot/perpetual carry engine")
    parser.add_argument("--config", default="carry_config.json")
    parser.add_argument("--data")
    parser.add_argument("--output-dir", default="carry_output")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if args.data:
        data = load_carry_csv(Path(args.data), str(config["symbol"]))
    else:
        data = fetch_public_carry_data(str(config["symbol"]), int(config.get("bars", 1500)))
        csv_path = output / f"{config['symbol']}_carry.csv"
        save_carry_csv(data, csv_path)
        data = load_carry_csv(csv_path, str(config["symbol"]))
    result = run_carry_backtest(data, config)
    (output / "latest_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (output / "latest_report.md").write_text(render_carry_report(result), encoding="utf-8")
    save_carry_paper_signal(
        result,
        output / "paper_signal.json",
        output / "paper_ledger.jsonl",
    )
    print(render_carry_report(result))


if __name__ == "__main__":
    main()
