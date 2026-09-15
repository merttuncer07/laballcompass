from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import verify_package


ROOT = Path(__file__).resolve().parent
ACTIVE_RESEARCH = ROOT / "ACTIVE_RESEARCH"
ACTIVE_PRODUCTS = ROOT / "ACTIVE_PRODUCTS"
BASE_R401 = ROOT / "BASE_R401"
R401_MATERIAL = (
    BASE_R401
    / "22_R399_R401_CURRENT_DELTA"
    / "LABALLCOMPASS_R401_MATERIAL_PRODUCT_REVIEW_2026-08-31"
    / "material_products"
)
R392_CORE = (
    BASE_R401
    / "18_R387_R393_CURRENT_POINT"
    / "06_EXACT_WORKTREE"
    / "01_V2_CORE"
)


def execute(label: str, cwd: Path, command: list[str]) -> dict:
    started = time.perf_counter()
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    output = completed.stdout + completed.stderr
    print(f"[{label}] exit={completed.returncode} seconds={time.perf_counter() - started:.3f}")
    if output.strip():
        print(output.rstrip())
    if completed.returncode:
        raise RuntimeError(f"reproduction target failed: {label}")
    pytest_match = re.search(r"(\d+) passed", output)
    unittest_match = re.search(r"Ran (\d+) tests?", output)
    count = int(pytest_match.group(1)) if pytest_match else (
        int(unittest_match.group(1)) if unittest_match else None
    )
    return {
        "label": label,
        "cwd": cwd.relative_to(ROOT).as_posix(),
        "command": command,
        "tests": count,
        "seconds": round(time.perf_counter() - started, 6),
        "status": "PASS",
    }


def run_active() -> list[dict]:
    rows: list[dict] = []
    round_pattern = re.compile(r"^R(?:19[3-9]|20[0-9]|210)_")
    rounds = sorted(path for path in ACTIVE_RESEARCH.iterdir() if path.is_dir() and round_pattern.match(path.name))
    if len(rounds) != 18:
        raise RuntimeError(f"expected 18 active round directories, found {len(rounds)}")
    for path in rounds:
        rows.append(execute(path.name, path, [sys.executable, "-m", "pytest", "-q"]))

    for name in ("LAB_CRYPTO_ALGOTRADER", "basin_authority_teacher_v001"):
        path = ACTIVE_PRODUCTS / name
        rows.append(execute(name, path, [sys.executable, "-m", "pytest", "-q"]))

    material_tests = (
        ("CONSEQUENCE_AWARE_INSPECTION_PLANNER", "test_planner.py"),
        ("TRIGGER_POLICY_DESIGNER", "test_trigger_designer.py"),
    )
    for name, test_file in material_tests:
        path = R401_MATERIAL / name
        rows.append(
            execute(
                f"R401_{name}",
                path,
                [sys.executable, "-m", "unittest", "-v", test_file],
            )
        )
    return rows


def run_embedded_r392() -> list[dict]:
    rows: list[dict] = []
    products = R392_CORE / "products"
    for path in sorted(products.glob("V2P*")):
        if path.is_dir() and any(path.glob("test_*.py")):
            rows.append(
                execute(
                    f"R392_{path.name}",
                    path,
                    [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py"],
                )
            )
    for test_file in sorted(R392_CORE.glob("test_*.py")):
        rows.append(
            execute(
                f"R392_CORE_{test_file.stem}",
                R392_CORE,
                [sys.executable, "-m", "unittest", "-v", test_file.name],
            )
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify and reproduce the LabAllCompass code package")
    parser.add_argument(
        "--profile",
        choices=("integrity", "active", "full"),
        default="active",
        help="integrity only; active 112-test surface; or active plus embedded R392 regression",
    )
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    if verify_package.main() != 0:
        return 1
    rows: list[dict] = []
    try:
        if args.profile in {"active", "full"}:
            rows.extend(run_active())
        if args.profile == "full":
            rows.extend(run_embedded_r392())
    except Exception as exc:
        receipt = {
            "profile": args.profile,
            "started_at_utc": started.isoformat(),
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "FAIL",
            "error": str(exc),
            "completed_targets": rows,
        }
        (ROOT / "REPRODUCTION_RUN_RECEIPT.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
        )
        raise

    receipt = {
        "profile": args.profile,
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "status": "PASS",
        "target_count": len(rows),
        "test_count": sum(row["tests"] or 0 for row in rows),
        "targets": rows,
    }
    (ROOT / "REPRODUCTION_RUN_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: receipt[key] for key in ("profile", "status", "target_count", "test_count")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

