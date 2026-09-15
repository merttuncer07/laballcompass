from __future__ import annotations
import argparse, json
from experiment_selector import load_contract, choose_next_experiment


def main() -> None:
    ap = argparse.ArgumentParser(description="Select the next quantified Lab experiment without leakage")
    ap.add_argument("--contract", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--telemetry-ledger")
    ap.add_argument("--calibration-output")
    ap.add_argument("--min-attempts", type=int, default=5)
    ap.add_argument("--min-axis-observations", type=int, default=5)
    args = ap.parse_args()
    contract = load_contract(args.contract)
    calibration = None
    if args.telemetry_ledger:
        from experiment_telemetry import ExperimentTelemetryLedger, compile_calibration_snapshot, hydrate_contract_from_calibration
        calibration = compile_calibration_snapshot(
            ExperimentTelemetryLedger.load_jsonl(args.telemetry_ledger),
            target_generation=contract.search_generation, problem_shell=contract.problem_shell,
            min_attempts=args.min_attempts, min_axis_observations=args.min_axis_observations,
        )
        contract = hydrate_contract_from_calibration(contract, calibration)
        if args.calibration_output:
            calibration.save(args.calibration_output)
    plan = choose_next_experiment(contract)
    plan.save(args.output)
    print(json.dumps({
        "selected_test_id": plan.selected_test_id, "stop": plan.stop,
        "stop_reason": plan.stop_reason, "blind_axes": plan.blind_axes,
        "calibration_snapshot_fingerprint": calibration.fingerprint if calibration else None,
    }, indent=2))


if __name__ == "__main__":
    main()
