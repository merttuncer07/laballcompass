from __future__ import annotations

import ast
import csv
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
ROOT = (
    WORKSPACE
    / "INPUT_FOUNDRY_RESCUE_AGENT_2026-08-25"
    / "LABALLCOMPASS_FOUNDRY_RESCUE_2026-08-25"
)
ARCHIVE = Path(
    r"C:\Users\mertt\OneDrive\Desktop\LABALLCOMPASS PRODUCTS IMPORTANT!!!!!!"
    r"\LABALLCOMPASS_FOUNDRY_RESCUE_2026-08-25.zip"
)
PREFIX = "LABALLCOMPASS_FOUNDRY_RESCUE_2026-08-25/"
OUTPUT = WORKSPACE / "lcb_core_revision" / "generated" / "agent_rescue_audit.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit_files(zf: zipfile.ZipFile) -> dict:
    files = sorted(
        (info for info in zf.infolist() if not info.is_dir()),
        key=lambda info: info.filename,
    )
    ext_counts: Counter[str] = Counter()
    ext_bytes: Counter[str] = Counter()
    ast_failures: list[dict[str, str]] = []
    byte_total = 0

    for info in files:
        data = zf.read(info)  # Deliberately read every salvaged file in full.
        byte_total += len(data)
        relative = info.filename.removeprefix(PREFIX)
        suffix = Path(relative).suffix.lower() or "<none>"
        ext_counts[suffix] += 1
        ext_bytes[suffix] += len(data)
        if suffix == ".py":
            try:
                ast.parse(data.decode("utf-8-sig"), filename=relative)
            except (SyntaxError, UnicodeDecodeError) as exc:
                ast_failures.append(
                    {"path": relative, "error": str(exc)}
                )

    return {
        "file_count": len(files),
        "bytes_read": byte_total,
        "extension_counts": dict(sorted(ext_counts.items())),
        "extension_bytes": dict(sorted(ext_bytes.items())),
        "python_ast_failures": ast_failures,
    }


def audit_manifest(zf: zipfile.ZipFile) -> dict:
    manifest_name = PREFIX + "00_MANIFESTS/FILES_SHA256.tsv"
    rows = list(
        csv.DictReader(zf.read(manifest_name).decode("utf-8").splitlines(), delimiter="\t")
    )
    names = {info.filename for info in zf.infolist() if not info.is_dir()}
    missing: list[str] = []
    mismatches: list[dict[str, object]] = []

    for row in rows:
        name = PREFIX + row["path"]
        if name not in names:
            missing.append(row["path"])
            continue
        data = zf.read(name)
        actual_size = len(data)
        actual_sha = sha256(data)
        if actual_size != int(row["size_bytes"]) or actual_sha != row["sha256"]:
            mismatches.append(
                {
                    "path": row["path"],
                    "expected_size": int(row["size_bytes"]),
                    "actual_size": actual_size,
                    "expected_sha256": row["sha256"],
                    "actual_sha256": actual_sha,
                }
            )

    listed = {row["path"] for row in rows}
    actual = {name.removeprefix(PREFIX) for name in names if name != manifest_name}
    return {
        "rows": len(rows),
        "missing": missing,
        "mismatches": mismatches,
        "unlisted_excluding_manifest_itself": sorted(actual - listed),
        "listed_but_not_actual": sorted(listed - actual),
    }


def audit_source_archives(zf: zipfile.ZipFile) -> dict:
    manifest_name = PREFIX + "00_MANIFESTS/SOURCE_ARCHIVE_SHA256.tsv"
    rows = list(
        csv.DictReader(zf.read(manifest_name).decode("utf-8").splitlines(), delimiter="\t")
    )
    results = []
    for row in rows:
        data = zf.read(PREFIX + "01_RAW_ARCHIVES/" + row["filename"])
        results.append(
            {
                "filename": row["filename"],
                "size_ok": len(data) == int(row["size_bytes"]),
                "sha256_ok": sha256(data) == row["sha256"],
            }
        )
    return {"archives": results}


def summarize_salvage_matrix(zf: zipfile.ZipFile) -> dict:
    name = PREFIX + "00_MANIFESTS/PRODUCT_SALVAGE_MATRIX.tsv"
    rows = list(csv.DictReader(zf.read(name).decode("utf-8").splitlines(), delimiter="\t"))
    statuses = Counter(row.get("status", "") for row in rows)
    materialized = [
        row.get("product", "")
        for row in rows
        if row.get("status") == "EXECUTABLE_MATERIALIZED"
    ]
    return {
        "rows": len(rows),
        "status_counts": dict(sorted(statuses.items())),
        "executable_materialized": materialized,
    }


def main() -> None:
    with zipfile.ZipFile(ARCHIVE) as zf:
        report = {
            "archive": str(ARCHIVE),
            "archive_sha256": sha256(ARCHIVE.read_bytes()),
            "all_files": audit_files(zf),
            "file_manifest": audit_manifest(zf),
            "source_archives": audit_source_archives(zf),
            "salvage_matrix": summarize_salvage_matrix(zf),
        }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    compact = {
        "archive_sha256": report["archive_sha256"],
        "file_count": report["all_files"]["file_count"],
        "bytes_read": report["all_files"]["bytes_read"],
        "python_ast_failures": len(report["all_files"]["python_ast_failures"]),
        "manifest_rows": report["file_manifest"]["rows"],
        "manifest_missing": len(report["file_manifest"]["missing"]),
        "manifest_mismatches": len(report["file_manifest"]["mismatches"]),
        "manifest_unlisted": len(report["file_manifest"]["unlisted_excluding_manifest_itself"]),
        "source_archives": report["source_archives"],
        "salvage_matrix": report["salvage_matrix"],
    }
    print(json.dumps(compact, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
