from __future__ import annotations

import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


ARCHIVE = Path(r"C:\Users\mertt\Downloads\LABALLCOMPASS_FINAL_RETIREMENT_HANDOFF_R398_2026-08-30.zip")
HERE = Path(__file__).resolve().parent
FILE_INDEX = HERE / "R401_ARCHIVE_FILE_INDEX.jsonl"
SUMMARY = HERE / "R401_ARCHIVE_FULL_SCAN.json"

TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".json", ".jsonl", ".tsv", ".csv", ".toml",
    ".yaml", ".yml", ".ini", ".cfg", ".status", ".log", ".ps1", ".bat",
    ".html", ".css", ".js", ".xml", ".rst", ".sha256",
}


def archive_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def category(name: str) -> str:
    lower = name.lower()
    base = Path(name).name.lower()
    if re.search(r"/(v2p\d{3}_[^/]+)/", lower):
        return "V2_PRODUCT"
    if "/parent_products/" in lower:
        return "PARENT_PRODUCT"
    if base.startswith("test_") or "/tests/" in lower:
        return "TEST"
    if "result" in base or "receipt" in base or "audit" in base:
        return "RESULT_EVIDENCE"
    if base in {"readme.md", "00_start_here.md", "00_read_me.md"} or "handoff" in base:
        return "DOCUMENTATION_HANDOFF"
    if Path(name).suffix.lower() == ".py":
        return "CODE"
    if Path(name).suffix.lower() in {".json", ".jsonl", ".csv", ".tsv"}:
        return "DATA_STATE"
    return "OTHER"


def decode_text(data: bytes, suffix: str) -> tuple[str | None, str | None]:
    if suffix not in TEXT_SUFFIXES and b"\x00" in data[:8192]:
        return None, None
    for encoding in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    return None, None


def main() -> None:
    if not ARCHIVE.exists():
        raise SystemExit(f"missing archive: {ARCHIVE}")
    total_uncompressed = 0
    extension_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    top_prefix_counts: Counter[str] = Counter()
    hash_counts: Counter[str] = Counter()
    text_files = 0
    binary_files = 0
    text_bytes = 0
    binary_bytes = 0
    decoded_by: Counter[str] = Counter()
    product_rows: dict[str, dict] = defaultdict(
        lambda: {
            "paths": 0,
            "bytes": 0,
            "python_files": 0,
            "test_files": 0,
            "test_methods": 0,
            "has_readme": False,
            "has_product_result": False,
            "has_composition": False,
            "composition_records": [],
        }
    )
    parent_rows: dict[str, dict] = defaultdict(
        lambda: {"paths": 0, "bytes": 0, "python_files": 0, "test_files": 0, "test_methods": 0, "has_product_result": False}
    )
    round_mentions: Counter[str] = Counter()
    mechanism_mentions: Counter[str] = Counter()
    parse_failures = []
    indexed = 0

    with zipfile.ZipFile(ARCHIVE) as archive, FILE_INDEX.open("w", encoding="utf-8") as index_handle:
        bad_crc = archive.testzip()
        if bad_crc is not None:
            raise RuntimeError(f"CRC failure: {bad_crc}")
        infos = [info for info in archive.infolist() if not info.is_dir()]
        for info in infos:
            data = archive.read(info)
            digest = hashlib.sha256(data).hexdigest()
            suffix = Path(info.filename).suffix.lower()
            text, encoding = decode_text(data, suffix)
            total_uncompressed += len(data)
            extension_counts[suffix or "<none>"] += 1
            category_counts[category(info.filename)] += 1
            top_prefix_counts[info.filename.split("/", 1)[0]] += 1
            hash_counts[digest] += 1
            record = {
                "path": info.filename,
                "bytes": len(data),
                "compressed_bytes": info.compress_size,
                "sha256": digest,
                "crc32": f"{info.CRC:08x}",
                "category": category(info.filename),
                "suffix": suffix,
                "is_text": text is not None,
            }
            if text is None:
                binary_files += 1
                binary_bytes += len(data)
            else:
                text_files += 1
                text_bytes += len(data)
                decoded_by[encoding or "unknown"] += 1
                lines = text.count("\n") + (1 if text else 0)
                test_methods = len(re.findall(r"(?m)^\s*def\s+test_[A-Za-z0-9_]+\s*\(", text))
                headings = re.findall(r"(?m)^#{1,3}\s+(.+?)\s*$", text)[:8]
                record.update(
                    {
                        "encoding": encoding,
                        "lines": lines,
                        "test_methods": test_methods,
                        "headings": headings,
                        "v2_ids": sorted(set(re.findall(r"\bV2P\d{3}\b", text)))[:30],
                        "round_ids": sorted(set(re.findall(r"\bR\d{3}\b", text)))[:30],
                        "im_ids": sorted(set(re.findall(r"\bIM[-_]?\d{3}\b", text)))[:30],
                    }
                )
                for rid in re.findall(r"\bR\d{3}\b", text):
                    round_mentions[rid] += 1
                for mid in re.findall(r"\b(?:IM[-_]?\d{3}|LCB-K\d{3}|FOUNDRY:P\d{3})\b", text):
                    mechanism_mentions[mid.replace("IM_", "IM-")] += 1

            product_match = re.search(r"/products/(V2P\d{3}_[^/]+)/", info.filename, re.I)
            if product_match:
                product = product_match.group(1).upper()
                row = product_rows[product]
                row["paths"] += 1
                row["bytes"] += len(data)
                row["python_files"] += suffix == ".py"
                row["test_files"] += Path(info.filename).name.lower().startswith("test_")
                row["test_methods"] += record.get("test_methods", 0)
                base = Path(info.filename).name.lower()
                row["has_readme"] |= base == "readme.md"
                row["has_product_result"] |= base == "product_result.md"
                row["has_composition"] |= base == "composition.json"
                if base == "composition.json" and text is not None:
                    try:
                        row["composition_records"].append(json.loads(text))
                    except Exception as exc:
                        parse_failures.append({"path": info.filename, "error": str(exc)})

            parent_match = re.search(r"/parent_products/(?:CURRENT_PRODUCTS|RETRO_PRODUCTS)/([^/]+)/", info.filename, re.I)
            if parent_match:
                parent = parent_match.group(1)
                row = parent_rows[parent]
                row["paths"] += 1
                row["bytes"] += len(data)
                row["python_files"] += suffix == ".py"
                row["test_files"] += Path(info.filename).name.lower().startswith("test_")
                row["test_methods"] += record.get("test_methods", 0)
                row["has_product_result"] |= Path(info.filename).name.lower() == "product_result.md"

            index_handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            indexed += 1

    duplicate_groups = sum(count > 1 for count in hash_counts.values())
    duplicate_files = sum(count for count in hash_counts.values() if count > 1)
    summary = {
        "model_version": "R401_ARCHIVE_FULL_SCAN_V1",
        "archive": str(ARCHIVE),
        "archive_sha256": archive_sha256(ARCHIVE),
        "zip_crc_all_entries": "PASS",
        "file_entries_read_in_full": indexed,
        "uncompressed_bytes_read": total_uncompressed,
        "text_files_read": text_files,
        "text_bytes_read": text_bytes,
        "binary_files_read": binary_files,
        "binary_bytes_read": binary_bytes,
        "decode_counts": dict(decoded_by),
        "extension_counts": dict(extension_counts.most_common()),
        "category_counts": dict(category_counts.most_common()),
        "top_prefix_counts": dict(top_prefix_counts.most_common()),
        "unique_content_hashes": len(hash_counts),
        "duplicate_content_groups": duplicate_groups,
        "files_in_duplicate_groups": duplicate_files,
        "v2_product_directories": len(product_rows),
        "v2_products": dict(sorted(product_rows.items())),
        "parent_product_directories": len(parent_rows),
        "parent_products": dict(sorted(parent_rows.items())),
        "round_mentions": dict(round_mentions.most_common()),
        "top_mechanism_mentions": dict(mechanism_mentions.most_common(250)),
        "json_parse_failures_for_compositions": parse_failures,
        "file_index": FILE_INDEX.name,
        "interpretation_boundary": "Every archive file was read and CRC-checked. The index records structural signals, not invented semantics.",
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "files": indexed,
                "uncompressed_bytes": total_uncompressed,
                "text_files": text_files,
                "binary_files": binary_files,
                "v2_product_directories": len(product_rows),
                "parent_product_directories": len(parent_rows),
                "archive_sha256": summary["archive_sha256"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
