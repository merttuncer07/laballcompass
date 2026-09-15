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
AUTHORITY = CORE / "CURRENT_PRODUCT_AUTHORITY.json"
OUTPUT = HERE / "R399_POSTPROMOTION_VERIFICATION.json"


def main() -> None:
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    rows = []
    for test_file in sorted(CORE.glob("test_*.py")):
        run = subprocess.run(
            [sys.executable, "-m", "unittest", test_file.stem],
            cwd=CORE,
            env=environment,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        output = run.stdout + run.stderr
        match = re.search(r"Ran (\d+) tests?", output)
        if run.returncode or not match:
            raise RuntimeError(f"postpromotion failure in {test_file.name}:\n{output[-5000:]}")
        rows.append({"surface": test_file.name, "tests": int(match.group(1))})

    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    if authority["authority_release"] != "R399":
        raise RuntimeError("R399 is not the active authority")
    mismatches = []
    for name, expected in authority["evidence_sha256"].items():
        path = LAB / name if name.startswith("R399_REPLAY/") else BASE / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            mismatches.append({"path": name, "expected": expected, "actual": actual})
    if mismatches:
        raise RuntimeError(f"authority evidence hash mismatches: {mismatches}")

    receipt = {
        "model_version": "R399_POSTPROMOTION_VERIFICATION_V1",
        "status": "PASS",
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "authority_release": "R399",
        "core_surface_count": len(rows),
        "core_test_count": sum(row["tests"] for row in rows),
        "failed": 0,
        "authority_evidence_files": len(authority["evidence_sha256"]),
        "authority_evidence_hash_mismatches": [],
        "rows": rows,
    }
    if receipt["core_surface_count"] != 17 or receipt["core_test_count"] != 153:
        raise RuntimeError(f"unexpected postpromotion totals: {receipt}")
    OUTPUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "authority_release", "core_surface_count", "core_test_count")}, indent=2))


if __name__ == "__main__":
    main()
