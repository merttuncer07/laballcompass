from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
LAB = HERE.parent
BASE = LAB / "R392_EXACT_BASE"
CORE = BASE / "01_V2_CORE"
PRODUCTS = CORE / "products"
AUTHORITY = CORE / "CURRENT_PRODUCT_AUTHORITY.json"
AUDIT = CORE / "PRODUCT_QUALITY_AUDIT_R399.json"
OVERLAY = CORE / "R399_PRODUCT_OVERLAY_STATE.json"
TELEMETRY = CORE / "generated_search" / "EXPERIMENT_TELEMETRY_INDEX_R12.json"
INTERACTION_MAP = CORE / "generated_search" / "INTERACTION_MAP_R12.json"
IDENTITY = HERE / "R399_INHERITED_BYTE_IDENTITY.json"
PILOT = HERE / "R399_LATE_PRODUCT_PILOT_RECEIPT.json"
RECEIPT = HERE / "R399_PROMOTION_REGRESSION_RECEIPT.json"
TRANSITION = HERE / "R399_AUTHORITY_TRANSITION.md"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_unittest(cwd: Path, arguments: list[str]) -> tuple[int, str]:
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", *arguments],
        cwd=cwd,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        timeout=180,
    )
    output = completed.stdout + completed.stderr
    if completed.returncode:
        raise RuntimeError(f"unittest failed in {cwd}:\n{output[-5000:]}")
    match = re.search(r"Ran (\d+) tests?", output)
    if not match:
        raise RuntimeError(f"could not count unittest cases in {cwd}:\n{output[-2000:]}")
    return int(match.group(1)), output


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def relative(path: Path) -> str:
    return path.relative_to(BASE).as_posix()


def main() -> None:
    started = datetime.now(timezone.utc)
    prior_authority = read_json(AUTHORITY)
    require(prior_authority["authority_release"] == "R392", "promotion must start from exact R392 authority")

    product_rows = []
    for product_dir in sorted(PRODUCTS.glob("V2P*")):
        match = re.match(r"^(V2P\d{3})_", product_dir.name)
        if not match or match.group(1) == "V2P047":
            continue
        tests, _ = run_unittest(product_dir, ["discover", "-s", ".", "-p", "test_*.py"])
        product_rows.append({"product_id": match.group(1), "directory": product_dir.name, "tests": tests})

    core_rows = []
    for test_file in sorted(CORE.glob("test_*.py")):
        tests, _ = run_unittest(CORE, [test_file.stem])
        core_rows.append({"surface": test_file.name, "tests": tests})

    identity_environment = os.environ.copy()
    identity_environment["PYTHONUTF8"] = "1"
    identity_run = subprocess.run(
        [sys.executable, str(HERE / "verify_inherited_identity.py")],
        cwd=HERE,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=identity_environment,
        timeout=180,
    )
    require(identity_run.returncode == 0, f"identity verification failed:\n{identity_run.stdout}\n{identity_run.stderr}")

    audit = read_json(AUDIT)
    telemetry = read_json(TELEMETRY)
    interaction_map = read_json(INTERACTION_MAP)
    identity = read_json(IDENTITY)
    pilot = read_json(PILOT)

    product_test_count = sum(row["tests"] for row in product_rows)
    core_test_count = sum(row["tests"] for row in core_rows)
    require(len(product_rows) == 57, f"expected 57 product suites, found {len(product_rows)}")
    require(product_test_count == 516, f"expected 516 product tests, found {product_test_count}")
    require(len(core_rows) == 17, f"expected 17 core surfaces, found {len(core_rows)}")
    require(core_test_count == 154, f"expected 154 core tests, found {core_test_count}")
    require(audit["resulting_executable_suite_count"] == 57, "audit executable suite count mismatch")
    require(audit["resulting_distinct_family_count"] == 44, "audit family count mismatch")
    require(telemetry["event_count"] == 516, "telemetry event count mismatch")
    require(telemetry["exact_current_suite_matches"] == 516, "telemetry exact-match mismatch")
    require(telemetry["unmatched_event_count"] == 0, "telemetry contains unmatched events")
    require(telemetry["current_completed_suite_count"] == 57, "telemetry current-suite mismatch")
    require(telemetry["calibrated_current_suite_count"] == 57, "telemetry calibration mismatch")
    require(interaction_map["edge_count"] == 16647, "interaction-map total mismatch")
    require(
        interaction_map["relation_counts"]
        == {
            "COMPLETED_COMPOSITION": 57,
            "INFERRED_CANDIDATE": 16532,
            "PARENT_OF": 53,
            "REJECTED_CURRENT_INTERFACE": 5,
        },
        "interaction-map relation counts mismatch",
    )
    require(identity["foundry"]["byte_identical"], "Foundry inheritance is not byte-identical")
    require(identity["foundry"]["archive_files"] == identity["foundry"]["local_files"] == 1305, "Foundry identity file count mismatch")
    require(identity["r392_canonical_products"]["byte_identical"], "R392 product inheritance is not byte-identical")
    require(
        identity["r392_canonical_products"]["archive_files"]
        == identity["r392_canonical_products"]["local_files"]
        == 421,
        "R392 identity file count mismatch",
    )
    require(pilot["event_count"] == 69, "late replay pilot event count mismatch")
    require(sum(row["events"] for row in pilot["products"]) == 69, "late replay per-product event mismatch")

    suite_ids = [row["product_id"] for row in product_rows]
    require(suite_ids == [f"V2P{number:03d}" for number in range(1, 59) if number != 47], "suite identity sequence mismatch")
    added_ids = ["V2P054", "V2P055", "V2P056", "V2P057", "V2P058"]
    family_ids = [*prior_authority["canonical_distinct_family_ids"], *added_ids]
    require(len(family_ids) == 44 and len(set(family_ids)) == 44, "distinct family identity mismatch")

    finished = datetime.now(timezone.utc)
    receipt = {
        "model_version": "R399_PROMOTION_REGRESSION_RECEIPT_V1",
        "status": "PASS",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": finished.isoformat(),
        "source_fidelity_boundary": {
            "byte_complete_base": "R392",
            "prior_logical_authority": "R397",
            "rehydrated_sources": "fresh R399 canonical bytes; not a claim of recovered R394-R398 bytes",
        },
        "direct_product_regression": {
            "suite_count": len(product_rows),
            "test_count": product_test_count,
            "failed": 0,
            "rows": product_rows,
        },
        "state_sensitive_core_regression": {
            "surface_count": len(core_rows),
            "test_count": core_test_count,
            "failed": 0,
            "rows": core_rows,
        },
        "inheritance": {
            "r392_product_files": 421,
            "foundry_files": 1305,
            "byte_identical": True,
        },
        "telemetry": {
            "events": 516,
            "exact_matches": 516,
            "unmatched": 0,
            "completed_suites": 57,
            "calibrated_suites": 57,
        },
        "interaction_map": {
            "completed": 57,
            "inferred": 16532,
            "parent_of": 53,
            "rejected": 5,
            "total": 16647,
        },
        "product_accounting": {"executable_suites": 57, "distinct_families": 44},
        "registry_family_count": 455,
        "registry455_unchanged": True,
        "quarantined_product_ids": ["V2P047"],
        "learning_eligible_campaign_events": 0,
    }
    write_json(RECEIPT, receipt)

    overlay = read_json(OVERLAY)
    overlay.update(
        {
            "status": "PROMOTED_TO_R399_PRODUCT_AUTHORITY",
            "promoted_as_authority_release": "R399",
            "promotion_regression_receipt": "../../R399_REPLAY/R399_PROMOTION_REGRESSION_RECEIPT.json",
        }
    )
    write_json(OVERLAY, overlay)

    audit["status"] = "PROMOTED_TO_R399_PRODUCT_AUTHORITY"
    audit["rules"] = [
        rule.replace("V2P058 remains candidate until explicit R399 authority transition", "V2P058 was admitted only after the explicit R399 promotion regression")
        for rule in audit["rules"]
    ]
    for row in audit["rows"]:
        if row["product_id"] == "V2P058":
            row["verdict"] = "REHYDRATED_DISTINCT_PRODUCT_PROMOTED_R399"
    write_json(AUDIT, audit)

    evidence_paths = [AUDIT, OVERLAY, TELEMETRY, INTERACTION_MAP, IDENTITY, PILOT, RECEIPT]
    authority = {
        "schema_version": 1,
        "status": "PROMOTED_CANONICAL_PRODUCT_AUTHORITY",
        "authority_release": "R399",
        "promoted_at_utc": finished.isoformat(),
        "prior_canonical_authority": {
            "byte_complete_release": "R392",
            "logical_receipt_supported_release": "R397",
            "executable_suites": 52,
            "distinct_families": 39,
        },
        "canonical_executable_suite_count": 57,
        "canonical_executable_suite_ids": suite_ids,
        "canonical_distinct_family_count": 44,
        "canonical_distinct_family_ids": family_ids,
        "new_r399_executable_suite_ids": added_ids,
        "new_r399_distinct_family_ids": added_ids,
        "registry_family_count": 455,
        "registry455_unchanged": True,
        "quarantined_product_ids": ["V2P047"],
        "promotion_basis": "Fresh R399 rehydration of V2P054-V2P058 passed exact direct, telemetry, graph-visibility, inherited-byte-identity and state-sensitive core regressions. Promotion establishes new canonical R399 bytes and does not claim recovery of lost R394-R398 source bytes.",
        "promotion_gates": {
            "direct_v2_test_files": 57,
            "direct_v2_tests_counted": 516,
            "direct_v2_failed": 0,
            "core_surfaces_fresh": 17,
            "core_tests_counted": 154,
            "telemetry_events": 516,
            "telemetry_exact_matches": 516,
            "telemetry_unmatched": 0,
            "calibrated_suites": 57,
            "interaction_map_completed_edges": 57,
            "candidate_universe_rows": 16594,
            "active_candidate_rows": 16589,
            "rejected_current_interface_edges": 5,
            "r392_inherited_product_files_byte_identical": 421,
            "foundry_inherited_files_byte_identical": 1305,
            "late_replay_tests_and_events": 69,
            "promotion_regression_bundle": "PASS",
        },
        "evidence_boundary": {
            "mechanics_telemetry_is_empirical_learning": False,
            "learning_eligible_campaign_events": 0,
            "statement": "Promotion certifies deterministic executable contracts, graph visibility, failure-region controls and internal family distinctness only; it is not novel-theory, scientific, financial, deployment or real-world validation.",
        },
        "evidence_sha256": {relative(path) if path.is_relative_to(BASE) else f"R399_REPLAY/{path.name}": sha256(path) for path in evidence_paths},
    }
    write_json(AUTHORITY, authority)

    TRANSITION.write_text(
        "# R399 Authority Transition\n\n"
        "R399 is promoted as the canonical product authority after a fresh state-sensitive regression. "
        "It contains 57 executable suites and 44 distinct product families; V2P047 remains quarantined.\n\n"
        "This is a rehydration transition, not a claim that the lost R394-R398 source bytes were recovered. "
        "The inherited R392 product tree (421 files) and Foundry tree (1,305 files) were checked byte-for-byte "
        "against the signed R398 handoff, while V2P054-V2P058 received fresh R399 identities and evidence.\n\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "authority_release": "R399", "product_tests": product_test_count, "core_tests": core_test_count}, indent=2))


if __name__ == "__main__":
    main()
