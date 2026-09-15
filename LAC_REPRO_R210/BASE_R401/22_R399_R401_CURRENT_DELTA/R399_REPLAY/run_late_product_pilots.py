"""Run fresh exact-shell mechanics pilots for the reconstructed V2P054–058.

These events calibrate executable contracts only.  They are not empirical
learning or evidence of real-world superiority.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "R392_EXACT_BASE" / "01_V2_CORE"
sys.path.insert(0, str(CORE))

from experiment_contract_bootstrap import (  # noqa: E402
    bootstrap_queue_row,
    discover_existing_composition_suites,
    run_fixed_suite_pilot,
)
from experiment_telemetry import ExperimentTelemetryLedger  # noqa: E402
from telemetry_registry import save_ledger  # noqa: E402


def main() -> int:
    suites = discover_existing_composition_suites(CORE)
    wanted = {f"V2P{number:03d}" for number in range(54, 59)}
    selected = sorted((pair, suite) for pair, suite in suites.items() if suite.product_id in wanted)
    if {suite.product_id for _, suite in selected} != wanted:
        raise RuntimeError("late replay suite discovery is incomplete")

    events = []
    receipts = []
    for pair, suite in selected:
        draft = bootstrap_queue_row(
            {"supplier_id": pair[0], "consumer_id": pair[1]},
            root=CORE,
            search_generation=399,
        )
        produced = run_fixed_suite_pilot(
            draft,
            release_generation=399,
            timeout_seconds=30.0,
            event_namespace="R399_REPLAY",
        )
        failures = [event.event_id for event in produced if event.run_status != "COMPLETE"]
        receipts.append({
            "product_id": suite.product_id,
            "supplier_id": pair[0],
            "consumer_id": pair[1],
            "test_signature": suite.test_signature,
            "problem_shell": suite.problem_shell,
            "events": len(produced),
            "complete": len(produced) - len(failures),
            "failures": failures,
        })
        events.extend(produced)

    if any(receipt["failures"] for receipt in receipts):
        raise RuntimeError("one or more late replay pilots failed")
    ledger_path = CORE / "search_data" / "EXPERIMENT_TELEMETRY.jsonl"
    replay_path = Path(__file__).with_name("R399_LATE_PRODUCT_TELEMETRY.jsonl")
    save_ledger(replay_path, ExperimentTelemetryLedger(events))
    current = ExperimentTelemetryLedger.load_jsonl(ledger_path)
    retained = [event for event in current.events if not event.event_id.startswith("R399_REPLAY::")]
    merged = ExperimentTelemetryLedger(sorted(retained + events, key=lambda event: event.event_id))
    save_ledger(ledger_path, merged)
    receipt_path = Path(__file__).with_name("R399_LATE_PRODUCT_PILOT_RECEIPT.json")
    receipt_path.write_text(json.dumps({
        "schema_version": 1,
        "status": "PASS",
        "event_count": len(events),
        "products": receipts,
        "evidence_boundary": "MECHANICS_EXACT_SHELL_NOT_EMPIRICAL_LEARNING",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "events": len(events), "ledger_events": len(merged.events)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
