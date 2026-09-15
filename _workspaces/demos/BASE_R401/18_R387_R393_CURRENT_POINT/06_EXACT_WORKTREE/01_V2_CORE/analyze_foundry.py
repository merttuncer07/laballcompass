from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


WORKSPACE = Path(r"C:\Users\mertt\OneDrive\Belgeler\ChatGPT\newlabexplore")
OUTER = (
    WORKSPACE
    / "INPUT_PRODUCT_FOUNDRY_P134_2026-08-25"
    / "HANDOFF_LABALLCOMPASS_PRODUCT_FOUNDRY_P134_2026-08-25"
)
BASE = (
    WORKSPACE
    / "INPUT_PRODUCT_FOUNDRY_BASE_P007_2026-08-25"
    / "LABALLCOMPASS_PRODUCT_INTERACTION_FOUNDRY_WORK"
)
OUT = WORKSPACE / "lcb_core_revision" / "generated"
OUTER_PRODUCTS = OUTER / "CURRENT_DELTA" / "03_OUTPUT" / "PRODUCTS"
BASE_PRODUCTS = BASE / "03_OUTPUT" / "PRODUCTS"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def scan_tree(root: Path) -> dict:
    files = sorted(p for p in root.rglob("*") if p.is_file())
    extensions = Counter()
    extension_bytes = Counter()
    hashes = {}
    python_errors = []
    total = 0
    for path in files:
        raw = path.read_bytes()
        rel = path.relative_to(root).as_posix()
        total += len(raw)
        extensions[path.suffix.lower() or "[none]"] += 1
        extension_bytes[path.suffix.lower() or "[none]"] += len(raw)
        hashes[rel] = digest(raw)
        if path.suffix.lower() == ".py":
            try:
                ast.parse(raw.decode("utf-8-sig"), filename=rel)
            except Exception as exc:
                python_errors.append({"file": rel, "error": repr(exc)})
    return {
        "root": str(root),
        "files_read_fully": len(files),
        "bytes_read": total,
        "extension_counts": dict(extensions),
        "extension_bytes": dict(extension_bytes),
        "python_parse_errors": python_errors,
        "sha256": hashes,
    }


def verify_outer_manifest() -> dict:
    rows = []
    for line in (OUTER / "SHA256SUMS.txt").read_text(encoding="utf-8-sig").splitlines():
        match = re.match(r"^([0-9a-f]{64})\s+\./(.+)$", line.strip(), re.I)
        if not match:
            continue
        expected, rel = match.groups()
        path = OUTER / rel
        actual = digest(path.read_bytes()) if path.exists() else "MISSING"
        rows.append({"file": rel, "expected": expected.lower(), "actual": actual, "match": expected.lower() == actual})
    return {
        "rows": len(rows),
        "matched": sum(r["match"] for r in rows),
        "mismatches": [r for r in rows if not r["match"]],
    }


def verify_base_manifest() -> dict:
    path = BASE / "MANIFEST_SHA256.tsv"
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            rel = row.get("path") or row.get("relative_path") or row.get("file")
            expected = (row.get("sha256") or row.get("hash") or "").lower()
            if not rel or not expected:
                continue
            target = BASE / rel
            actual = digest(target.read_bytes()) if target.exists() else "MISSING"
            rows.append({"file": rel, "expected": expected, "actual": actual, "match": expected == actual})
    return {
        "rows": len(rows),
        "matched": sum(r["match"] for r in rows),
        "mismatches": [r for r in rows if not r["match"]],
    }


def sections(text: str) -> dict[str, str]:
    output: dict[str, list[str]] = {"_preamble": []}
    current = "_preamble"
    for line in text.splitlines():
        match = re.match(r"^#{2,6}\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip().lower()
            output.setdefault(current, [])
        else:
            output.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in output.items()}


def first_available(parts: dict[str, str], names: tuple[str, ...]) -> str:
    for name in names:
        for key, value in parts.items():
            if name in key and value:
                return value
    return ""


def product_record(path: Path, origin: str) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    match = re.fullmatch(r"P(\d{3})_([A-Z0-9]+)", path.parent.name)
    if not match:
        match = re.search(r"P(\d{3})\s+([A-Z0-9]+)", text)
    pid = f"P{match.group(1)}" if match else "UNKNOWN"
    short = match.group(2) if match else "UNKNOWN"
    title_match = re.search(r"(?m)^#\s+(.+)$", text)
    title = title_match.group(1).strip() if title_match else f"{pid} {short}"
    parts = sections(text)
    parents_match = re.search(r"(?im)^\*\*Parents?:\*\*\s*(.+)$", text)
    if not parents_match:
        parents_match = re.search(r"(?im)^Parents?:\s*\*\*(.+?)\*\*\s*$", text)
    composition = first_available(parts, ("composition",))
    parents = parents_match.group(1).strip() if parents_match else (composition.splitlines()[0] if composition else "UNEXTRACTED")
    status_match = re.search(r"(?im)^(?:\*\*)?(?:promotion state|status)(?:\*\*)?:?\s*\*\*?`?([^\n*`]+)", text)
    status = status_match.group(1).strip() if status_match else "UNEXTRACTED"
    strength = first_available(parts, ("new capability", "what materially changed", "composition", "product"))
    weakness = first_available(parts, ("claim boundary", "boundary", "limitation", "failure"))
    evidence = first_available(parts, ("benchmark", "measured evidence", "result", "verification"))
    product_dir = path.parent
    source_files = sorted(
        p.name for p in product_dir.glob("*.py") if not p.name.startswith("test_") and p.name != "__init__.py"
    )
    test_files = sorted(p.name for p in product_dir.glob("test_*.py"))
    return {
        "product_id": pid,
        "short_name": short,
        "title": title,
        "origin": origin,
        "relative_path": path.as_posix(),
        "parents_raw": parents,
        "promotion_state": status,
        "strength_raw": strength,
        "weakness_raw": weakness,
        "evidence_raw": evidence,
        "has_explicit_strength": bool(strength),
        "has_explicit_weakness": bool(weakness),
        "source_files": source_files,
        "test_files": test_files,
        "executable_source_present": bool(source_files),
        "test_source_present": bool(test_files),
    }


def catalog_products() -> list[dict]:
    records: dict[str, dict] = {}
    for path in sorted(BASE_PRODUCTS.glob("P*/PRODUCT_RESULT.md")):
        row = product_record(path, "BASE_FOUNDATION")
        records[row["product_id"]] = row
    for path in sorted(OUTER_PRODUCTS.glob("P*/PRODUCT_RESULT.md")):
        row = product_record(path, "CURRENT_DELTA")
        previous = records.get(row["product_id"])
        if previous:
            row["source_files"] = sorted(set(previous["source_files"] + row["source_files"]))
            row["test_files"] = sorted(set(previous["test_files"] + row["test_files"]))
            row["executable_source_present"] = bool(row["source_files"])
            row["test_source_present"] = bool(row["test_files"])
            row["origin"] = "BASE_FOUNDATION+CURRENT_DELTA"
        records[row["product_id"]] = row
    return sorted(records.values(), key=lambda r: int(r["product_id"][1:]) if r["product_id"] != "UNKNOWN" else 9999)


def interface_registry() -> list[dict]:
    return json.loads((BASE / "03_OUTPUT" / "INTERFACE_CAPABILITY_REGISTRY.json").read_text(encoding="utf-8"))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    outer_audit = scan_tree(OUTER)
    base_audit = scan_tree(BASE)
    outer_manifest = verify_outer_manifest()
    base_manifest = verify_base_manifest()
    products = catalog_products()
    interfaces = interface_registry()
    available = [
        line.strip()
        for line in (OUTER / "AVAILABLE_PRODUCT_ARTIFACTS.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    materialized_ids = {re.match(r"P\d{3}", name).group(0) for name in available if re.match(r"P\d{3}", name)}
    all_ids = {f"P{i:03d}" for i in range(1, 135)}

    audit = {
        "outer": {k: v for k, v in outer_audit.items() if k != "sha256"},
        "base": {k: v for k, v in base_audit.items() if k != "sha256"},
        "combined_files_read_fully": outer_audit["files_read_fully"] + base_audit["files_read_fully"],
        "combined_bytes_read": outer_audit["bytes_read"] + base_audit["bytes_read"],
        "outer_manifest": outer_manifest,
        "base_manifest": base_manifest,
        "parent_interface_records": len(interfaces),
        "product_result_records": len(products),
        "available_materialized_product_ids": len(materialized_ids),
        "missing_materialized_product_ids": sorted(all_ids - materialized_ids),
        "product_records_with_executable_source": sum(r["executable_source_present"] for r in products),
        "product_records_with_test_source": sum(r["test_source_present"] for r in products),
        "product_records_with_explicit_strength": sum(r["has_explicit_strength"] for r in products),
        "product_records_with_explicit_weakness": sum(r["has_explicit_weakness"] for r in products),
    }
    (OUT / "foundry_source_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "FOUNDRY_PRODUCT_CATALOG.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in products) + "\n", encoding="utf-8"
    )
    (OUT / "FOUNDRY_PARENT_INTERFACE_REGISTRY.json").write_text(
        json.dumps(interfaces, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    fields = [
        "product_id", "short_name", "title", "origin", "parents_raw", "promotion_state",
        "has_explicit_strength", "has_explicit_weakness", "executable_source_present", "test_source_present",
        "strength_raw", "weakness_raw",
    ]
    with (OUT / "FOUNDRY_PRODUCT_CATALOG.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(products)
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
