from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run_file(path: Path) -> dict[str, object]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    source = path.read_text(encoding="utf-8-sig")
    function_style = "def test_" in source and "unittest" not in source
    if function_style:
        module = ".".join(path.relative_to(ROOT).with_suffix("").parts)
        command = [
            sys.executable,
            str(ROOT / "run_function_test_module.py"),
            module,
        ]
        cwd = ROOT
    else:
        command = [sys.executable, path.name]
        cwd = path.parent
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
    )
    combined = completed.stdout + "\n" + completed.stderr
    matches = re.findall(r"Ran\s+(\d+)\s+tests?", combined)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "returncode": completed.returncode,
        "tests": int(matches[-1]) if matches else None,
        "output": combined[-4000:] if completed.returncode else "",
    }


def main() -> int:
    parent_tests = sorted((ROOT / "parent_products").rglob("test_*.py"))
    product_tests = sorted(
        path
        for path in (ROOT / "products").rglob("test_*.py")
        if path.name != "test_reig.py"  # original historical test requires external pytest
    )
    results = [run_file(path) for path in parent_tests + product_tests]
    summary = {
        "parent_test_files": len(parent_tests),
        "product_test_files": len(product_tests),
        "test_files_passed": sum(result["returncode"] == 0 for result in results),
        "test_files_failed": sum(result["returncode"] != 0 for result in results),
        "tests_counted": sum(result["tests"] or 0 for result in results),
        "results": results,
    }
    output = ROOT / "regression_summary.json"
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "results"}, indent=2))
    for result in results:
        if result["returncode"]:
            print(f"FAILED: {result['path']}")
            print(result["output"])
    return 1 if summary["test_files_failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
