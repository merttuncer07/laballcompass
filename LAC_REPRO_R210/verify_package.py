from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import sys


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "04_FILE_MANIFEST_SHA256.tsv"
REQUIRED = (
    "00_START_HERE.md",
    "01_SCOPE_AND_PROVENANCE.md",
    "02_PACKAGE_INVENTORY.json",
    "03_TEST_MATRIX.tsv",
    "05_PREBUILD_TEST_RECEIPT.json",
    "requirements-reproduction.txt",
    "run_reproduction.py",
    "BASE_R401/18_R387_R393_CURRENT_POINT",
    "BASE_R401/19_R394_R398_FINAL_RETIREMENT_DELTA",
    "BASE_R401/20_SURVIVING_POST_R393_SURFACED_FILES",
    "BASE_R401/22_R399_R401_CURRENT_DELTA",
    "ACTIVE_RESEARCH/R193_MARKOV_OMITTED_EVENT_COMPILER",
    "ACTIVE_RESEARCH/R210_SECOND_PASS_BOUNDARIES",
    "ACTIVE_PRODUCTS/LAB_CRYPTO_ALGOTRADER",
    "ACTIVE_PRODUCTS/basin_authority_teacher_v001",
    "REPORT/LABALLCOMPASS_R193_R208_AKADEMIK_RAPOR.md",
    "REPORT/LABALLCOMPASS_R193_R208_AKADEMIK_RAPOR.docx",
    "REPORT/LABALLCOMPASS_R193_R208_AKADEMIK_RAPOR.pdf",
)
IGNORED_PARTS = {"__pycache__", ".pytest_cache"}
IGNORED_FILES = {".DS_Store"}


def io_path(path: Path) -> Path:
    if os.name == "nt":
        absolute = str(path.absolute())
        if not absolute.startswith("\\\\?\\"):
            return Path("\\\\?\\" + absolute)
    return path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with io_path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    errors: list[str] = []
    if not MANIFEST.is_file():
        print("PACKAGE VERIFY: FAIL\n- missing 04_FILE_MANIFEST_SHA256.tsv")
        return 1

    for relative in REQUIRED:
        if not io_path(ROOT / relative).exists():
            errors.append(f"missing required path: {relative}")

    rows = []
    with MANIFEST.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected = ["path", "sha256", "bytes", "component"]
        if reader.fieldnames != expected:
            errors.append(f"unexpected manifest schema: {reader.fieldnames}")
        else:
            rows = list(reader)

    checked = 0
    total_bytes = 0
    seen: set[str] = set()
    forbidden = re.compile(
        r"(?:^|/)(?:POST_R178_SALVAGE_ARCHIVE|R(?:179|180|181|182|183|184|185|186|187|188|189|190|191|192)(?:_|/))|bridge|regime.?router|laballcompass.?skill",
        re.IGNORECASE,
    )
    actual_files: set[str] = set()
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT).as_posix()
        if forbidden.search(relative):
            errors.append(f"retired/discarded path present: {relative}")
        if not path.is_file() or path.name in IGNORED_FILES or any(part in IGNORED_PARTS for part in path.parts):
            continue
        if path.suffix in (".pyc", ".pyo") or relative == MANIFEST.name:
            continue
        actual_files.add(relative)
    for row in rows:
        relative = row["path"]
        logical = PurePosixPath(relative)
        if logical.is_absolute() or ".." in logical.parts or logical.as_posix() != relative:
            errors.append(f"unsafe or non-canonical manifest path: {relative}")
            continue
        if relative in seen:
            errors.append(f"duplicate manifest path: {relative}")
            continue
        seen.add(relative)
        if forbidden.search(relative):
            errors.append(f"retired/discarded path packaged: {relative}")
            continue
        path = ROOT / Path(relative)
        target = io_path(path)
        if not target.is_file():
            errors.append(f"missing manifest file: {relative}")
            continue
        actual_bytes = target.stat().st_size
        expected_bytes = int(row["bytes"])
        if actual_bytes != expected_bytes:
            errors.append(f"size mismatch: {relative}")
            continue
        if sha256(path) != row["sha256"]:
            errors.append(f"hash mismatch: {relative}")
            continue
        checked += 1
        total_bytes += actual_bytes

    for relative in sorted(actual_files - seen):
        errors.append(f"unmanifested package file: {relative}")

    if errors:
        print("PACKAGE VERIFY: FAIL")
        for error in errors[:50]:
            print(f"- {error}")
        if len(errors) > 50:
            print(f"- ... {len(errors) - 50} more")
        return 1

    print("PACKAGE VERIFY: PASS")
    print(f"files={checked} bytes={total_bytes}")
    print("retired_bridge_router_skill=absent discarded_R179_R192=absent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
