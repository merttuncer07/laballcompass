from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(label: str, cwd: Path, script: str) -> dict:
    completed = subprocess.run(
        [sys.executable, script],
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    return {
        "label": label,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def main() -> None:
    v2 = ROOT / "01_V2_CORE"
    # R388 visibility rule: the regression authority must discover every current V2
    # executable test surface instead of hard-coding an ID prefix.  The product
    # directory is the source of truth for physical executable-suite coverage.
    runs = [
        run("foundry_806", ROOT / "02_FOUNDRY_ALL_PRODUCTS", "run_regression.py"),
        run("core_v2", v2, "test_core_v2.py"),
        run("foundry_integration", v2, "test_core_v2_foundry_integration.py"),
        run("search_engine", v2, "test_lab_search_engine.py"),
        run("search_corpus", v2, "test_search_corpus_integration.py"),
        run("relevance_learning", v2, "test_relevance_learning.py"),
        run("experiment_selector", v2, "test_experiment_selector.py"),
        run("experiment_telemetry", v2, "test_experiment_telemetry.py"),
        run("experiment_integration", v2, "test_experiment_integration.py"),
        run("experiment_contract_bootstrap", v2, "test_experiment_contract_bootstrap.py"),
    ]
    product_test_files = sorted((v2 / "products").glob("V2P*/test_*.py"))
    for test_path in product_test_files:
        product_dir = test_path.parent
        runs.append(run(f"v2_product::{product_dir.name}/{test_path.name}", product_dir, test_path.name))
    runs.extend([
        run("r12_closure_updated", v2, "test_r12_closure.py"),
        run("r387_product_overlay_history", v2, "test_r387_product_overlay_closure.py"),
        run("r388_retro50_parent_integration_closure", v2, "test_r388_retro50_parent_integration_closure.py"),
        run("r389_product_overlay_closure", v2, "test_r389_product_overlay_closure.py"),
    ])
    report = {"status": "PASS" if all(r["exit_code"] == 0 for r in runs) else "FAIL", "runs": runs}
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
