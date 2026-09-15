"""Verify unchanged R392 product and Foundry bytes against the signed R398 ZIP."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "R392_EXACT_BASE"
DEFAULT_ARCHIVE = Path.home() / "Downloads" / "LABALLCOMPASS_FINAL_RETIREMENT_HANDOFF_R398_2026-08-30.zip"
ARCHIVE_PREFIX = "LABALLCOMPASS_FINAL_RETIREMENT_HANDOFF_R398_2026-08-30/18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE/"


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_relative_files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }


def compare_prefix(archive: zipfile.ZipFile, relative_prefix: str, local_root: Path, selector=None) -> dict:
    prefix = ARCHIVE_PREFIX + relative_prefix.rstrip("/") + "/"
    entries = {}
    for info in archive.infolist():
        if info.is_dir() or not info.filename.startswith(prefix):
            continue
        relative = info.filename[len(prefix):]
        if selector is not None and not selector(relative):
            continue
        entries[relative] = info
    local = local_relative_files(local_root)
    if selector is not None:
        local = {relative for relative in local if selector(relative)}
    missing = sorted(set(entries) - local)
    extra = sorted(local - set(entries))
    changed = []
    for relative, info in sorted(entries.items()):
        path = local_root / Path(relative)
        if not path.exists():
            continue
        if path.stat().st_size != info.file_size or digest_bytes(path.read_bytes()) != digest_bytes(archive.read(info)):
            changed.append(relative)
    return {
        "archive_files": len(entries),
        "local_files": len(local),
        "missing": missing,
        "extra": extra,
        "changed": changed,
        "byte_identical": not missing and not extra and not changed,
    }


def old_product(relative: str) -> bool:
    match = re.match(r"(V2P(\d{3})_[^/]+)/", relative)
    return bool(match and int(match.group(2)) <= 53 and int(match.group(2)) != 47)


def main() -> int:
    archive_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ARCHIVE
    if not archive_path.is_file():
        raise FileNotFoundError(archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        foundry = compare_prefix(archive, "02_FOUNDRY_ALL_PRODUCTS", BASE / "02_FOUNDRY_ALL_PRODUCTS")
        products = compare_prefix(archive, "01_V2_CORE/products", BASE / "01_V2_CORE" / "products", old_product)
    payload = {
        "schema_version": 1,
        "archive": str(archive_path),
        "archive_sha256": digest_bytes(archive_path.read_bytes()),
        "foundry": foundry,
        "r392_canonical_products": products,
        "status": "PASS" if foundry["byte_identical"] and products["byte_identical"] else "FAIL",
    }
    output = Path(__file__).with_name("R399_INHERITED_BYTE_IDENTITY.json")
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
