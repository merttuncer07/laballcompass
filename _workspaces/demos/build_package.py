from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile


SOURCE_DIR = Path(__file__).resolve().parent
REPO = SOURCE_DIR.parents[1]
PACKAGE_NAME = "LABALLCOMPASS_REPRO_R210_2026-09-01"
ARCHIVE_ROOT = "LAC_REPRO_R210"
OUTPUT_DIR = REPO / "output" / "reproduction"
ZIP_PATH = OUTPUT_DIR / f"{PACKAGE_NAME}.zip"
SHA_PATH = OUTPUT_DIR / f"{PACKAGE_NAME}.sha256.txt"
R401 = REPO / "LABALLCOMPASS_R401_MATERIAL_PRODUCT_HANDOFF_2026-08-31"
R401_MANIFEST = R401 / "24_R401_INTEGRITY_SHA256.tsv"
MANIFEST_NAME = "04_FILE_MANIFEST_SHA256.tsv"

STATIC_FILES = (
    "00_START_HERE.md",
    "01_SCOPE_AND_PROVENANCE.md",
    "03_TEST_MATRIX.tsv",
    "05_PREBUILD_TEST_RECEIPT.json",
    "requirements-reproduction.txt",
    "verify_package.py",
    "run_reproduction.py",
    "build_package.py",
)
R401_PREFIXES = (
    "18_R387_R393_CURRENT_POINT/",
    "19_R394_R398_FINAL_RETIREMENT_DELTA/",
    "20_SURVIVING_POST_R393_SURFACED_FILES/",
    "22_R399_R401_CURRENT_DELTA/",
)
R401_TOP_FILES = {
    "00_START_HERE_R401.md",
    "00_START_HERE.md",
    "01_ARCHITECTURE_BLUEPRINT.md",
    "02_CANONICAL_CURRENT_STATE.json",
    "03_CHRONOLOGY_R1_R393.md",
    "04_AUTHORITY_AND_STATUS_LEDGER.tsv",
    "05_ENTITY_GENEALOGY.jsonl",
    "06_REGISTRY_PRODUCTS_AND_CATEGORIES.md",
    "08_REPRODUCIBILITY_AND_BOOTSTRAP.md",
    "10_DEPENDENCY_NOTES.md",
    "21_FINAL_PACKAGE_MAP.md",
    "23_R401_PACKAGE_MAP.md",
    "26_R401_OMISSIONS.tsv",
}
R202_CONTEXT_FILES = (
    "01_ROOT_AND_TRANSFORMATION_REPORT.md",
    "02_STANDALONE_RESEARCH_METHODOLOGY.md",
    "03_CURRENT_FRONTIER_AND_RESUME.md",
    "04_CLAIM_STATUS_LEDGER.tsv",
    "05_FREEZE_STATE.json",
    "06_REPRODUCIBILITY.md",
    "09_OMISSIONS.tsv",
    "11_SCIENCE_TEST_RECEIPT.json",
)
SKIP_PARTS = {"__pycache__", ".pytest_cache", ".git", ".venv", "venv"}
FORBIDDEN = re.compile(
    r"(?:^|/)(?:POST_R178_SALVAGE_ARCHIVE|R(?:179|180|181|182|183|184|185|186|187|188|189|190|191|192)(?:_|/))|bridge|regime.?router|laballcompass.?skill",
    re.IGNORECASE,
)


def io_name(path: Path) -> str:
    absolute = str(path.absolute())
    if os.name == "nt" and not absolute.startswith("\\\\?\\"):
        return "\\\\?\\" + absolute
    return absolute


def digest(path: Path) -> tuple[str, int]:
    result = hashlib.sha256()
    size = 0
    with open(io_name(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            result.update(chunk)
    return result.hexdigest(), size


def entry(source: Path, relative: str, component: str, known_hash: str | None = None, known_bytes: int | None = None) -> dict:
    normalized = PurePosixPath(relative).as_posix()
    if FORBIDDEN.search(normalized):
        raise RuntimeError(f"retired/discarded path refused: {normalized}")
    if known_hash is None or known_bytes is None:
        known_hash, known_bytes = digest(source)
    return {
        "source": source,
        "path": normalized,
        "sha256": known_hash,
        "bytes": int(known_bytes),
        "component": component,
    }


def tree_entries(source_root: Path, package_root: str, component: str) -> list[dict]:
    rows: list[dict] = []
    root_name = io_name(source_root)
    for current, directories, files in os.walk(root_name):
        directories[:] = sorted(name for name in directories if name not in SKIP_PARTS)
        for name in sorted(files):
            if name.endswith((".pyc", ".pyo")):
                continue
            source_text = os.path.join(current, name)
            relative = os.path.relpath(source_text, root_name).replace("\\", "/")
            logical_source = source_root / Path(relative)
            rows.append(entry(logical_source, f"{package_root}/{relative}", component))
    return rows


def selected_r401_entries() -> list[dict]:
    rows: list[dict] = []
    with R401_MANIFEST.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != ["path", "sha256", "bytes"]:
            raise RuntimeError("unexpected R401 manifest schema")
        for item in reader:
            relative = item["path"].replace("\\", "/")
            if not (relative in R401_TOP_FILES or relative.startswith(R401_PREFIXES)):
                continue
            if any(part in SKIP_PARTS for part in PurePosixPath(relative).parts):
                continue
            if relative.endswith((".pyc", ".pyo")):
                continue
            rows.append(
                entry(
                    R401 / Path(relative),
                    f"BASE_R401/{relative}",
                    "base_r401_active_product_payload",
                    item["sha256"],
                    int(item["bytes"]),
                )
            )
    return rows


def source_entries() -> list[dict]:
    rows: list[dict] = []
    for name in STATIC_FILES:
        rows.append(entry(SOURCE_DIR / name, name, "package_tools"))

    rows.extend(selected_r401_entries())

    work = REPO / "TURING_ALLCOMPASS_MACHINE" / "NEW_WORK"
    round_pattern = re.compile(r"^R(?:19[3-9]|20[0-9]|210)_")
    rounds = sorted(path for path in work.iterdir() if path.is_dir() and round_pattern.match(path.name))
    if len(rounds) != 18:
        raise RuntimeError(f"expected 18 active R193-R210 directories, found {len(rounds)}")
    for path in rounds:
        rows.extend(tree_entries(path, f"ACTIVE_RESEARCH/{path.name}", "active_research_R193_R210"))

    products = (
        (REPO / "PRODUCTS" / "LAB_CRYPTO_ALGOTRADER", "LAB_CRYPTO_ALGOTRADER"),
        (REPO / "lab_products" / "basin_authority_teacher_v001", "basin_authority_teacher_v001"),
    )
    for path, name in products:
        rows.extend(tree_entries(path, f"ACTIVE_PRODUCTS/{name}", "active_products"))

    report_dir = REPO / "LAB_REPORTS" / "R208_ACTIVE_THEORY_PORTFOLIO"
    report_files = (
        report_dir / "LABALLCOMPASS_R193_R208_AKADEMIK_RAPOR.md",
        report_dir / "LABALLCOMPASS_R193_R208_AKADEMIK_RAPOR.docx",
        REPO / "output" / "pdf" / "LABALLCOMPASS_R193_R208_AKADEMIK_RAPOR.pdf",
        report_dir / "build_report.py",
        report_dir / "build_report_pdf.py",
    )
    for path in report_files:
        rows.append(entry(path, f"REPORT/{path.name}", "academic_report"))

    context = REPO / "LABALLCOMPASS_R202_THEORY_REVISIT_FREEZE_2026-08-31"
    for name in R202_CONTEXT_FILES:
        rows.append(entry(context / name, f"R202_CONTEXT/{name}", "methodology_context"))

    rows.append(entry(REPO / "AGENTS.md", "CONTRACT/AGENTS.md", "repository_contract"))
    return rows


def write_inventory(rows: list[dict]) -> Path:
    stats: dict[str, dict[str, int]] = {}
    for row in rows:
        item = stats.setdefault(row["component"], {"files": 0, "bytes": 0})
        item["files"] += 1
        item["bytes"] += row["bytes"]
    payload = {
        "package": PACKAGE_NAME,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "active executable/product code plus R193-R210 research and report reproduction",
        "manifest_semantics": "all packaged files except 04_FILE_MANIFEST_SHA256.tsv",
        "source_rows_before_generated_inventory": len(rows),
        "source_bytes_before_generated_inventory": sum(row["bytes"] for row in rows),
        "components": stats,
        "excluded": [
            "Bridge",
            "Regime Router",
            "retired custom Lab skill/control plane",
            "discarded R179-R192 branch",
            "POST_R178_SALVAGE_ARCHIVE",
            "R401 historical source/case-library and duplicate current-point layers",
            "virtual environments and regenerable post-R401 caches",
        ],
    }
    target = SOURCE_DIR / "02_PACKAGE_INVENTORY.json"
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


def write_manifest(rows: list[dict]) -> Path:
    target = SOURCE_DIR / MANIFEST_NAME
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["path", "sha256", "bytes", "component"])
        for row in sorted(rows, key=lambda item: item["path"]):
            writer.writerow([row["path"], row["sha256"], row["bytes"], row["component"]])
    return target


def zip_timestamp(path: Path) -> tuple[int, int, int, int, int, int]:
    stamp = datetime.fromtimestamp(os.stat(io_name(path)).st_mtime)
    year = max(1980, min(2107, stamp.year))
    return year, stamp.month, stamp.day, stamp.hour, stamp.minute, stamp.second


def add_to_zip(archive: zipfile.ZipFile, source: Path, relative: str) -> None:
    info = zipfile.ZipInfo(f"{ARCHIVE_ROOT}/{relative}", date_time=zip_timestamp(source))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    with open(io_name(source), "rb") as src, archive.open(info, "w", force_zip64=True) as dst:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            dst.write(chunk)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true", help="replace only this package's existing ZIP/checksum")
    args = parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists() and not args.replace:
        raise FileExistsError(f"output exists; pass --replace: {ZIP_PATH}")
    if args.replace:
        for path in (ZIP_PATH, SHA_PATH):
            if path.exists():
                path.unlink()

    rows = source_entries()
    inventory = write_inventory(rows)
    rows.append(entry(inventory, inventory.name, "package_tools"))
    seen: set[str] = set()
    for row in rows:
        if row["path"] in seen:
            raise RuntimeError(f"duplicate package path: {row['path']}")
        seen.add(row["path"])
    manifest = write_manifest(rows)

    with zipfile.ZipFile(ZIP_PATH, "w", allowZip64=True) as archive:
        for index, row in enumerate(sorted(rows, key=lambda item: item["path"]), start=1):
            add_to_zip(archive, row["source"], row["path"])
            if index % 500 == 0:
                print(f"packaged {index}/{len(rows)} files", flush=True)
        add_to_zip(archive, manifest, MANIFEST_NAME)

    zip_hash, zip_bytes = digest(ZIP_PATH)
    SHA_PATH.write_text(f"{zip_hash}  {ZIP_PATH.name}\n", encoding="utf-8")
    print(json.dumps({
        "zip": str(ZIP_PATH),
        "sha256": zip_hash,
        "zip_bytes": zip_bytes,
        "manifest_files": len(rows),
        "manifest_bytes": sum(row["bytes"] for row in rows),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
