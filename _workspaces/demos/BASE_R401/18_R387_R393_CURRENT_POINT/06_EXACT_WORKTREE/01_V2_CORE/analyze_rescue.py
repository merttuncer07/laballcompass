from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


WORKSPACE = Path(r"C:\Users\mertt\OneDrive\Belgeler\ChatGPT\newlabexplore")
SOURCE = WORKSPACE / "INPUT_LCB_7F3A91_R50_PARTIAL_2026-08-25"
OUT = WORKSPACE / "lcb_core_revision" / "generated"
CORE_FILE = SOURCE / "r49_checkpoint" / "prototypes" / (
    "LABCOMPASS__LCB-7F3A91__20260825-1048-TR__PRODUCT_PROTOTYPES__r38.py"
)
QUEUE_FILE = SOURCE / "r49_checkpoint" / "registries_queues" / (
    "LABCOMPASS__LCB-7F3A91__20260825-1048-TR__CROSS_DOMAIN_TRANSFER_QUEUE_ADJUDICATED__r49.tsv"
)
RESCORE_FILE = SOURCE / "r49_checkpoint" / "registries_queues" / (
    "LABCOMPASS__LCB-7F3A91__20260825-1048-TR__VALUE_FIRST_RESCORING_ALL_211__r23.tsv"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def preceding_marker(lines: list[str], lineno: int) -> str | None:
    start = max(0, lineno - 12)
    for line in reversed(lines[start : lineno - 1]):
        stripped = line.strip()
        if stripped.startswith("# ----") or stripped.startswith("# Added"):
            return stripped.lstrip("# ").strip("- ")
        if stripped.startswith("class "):
            break
    return None


def class_registry(queue: list[dict[str, str]], rescore: dict[str, dict[str, str]]) -> list[dict]:
    text = CORE_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    tree = ast.parse(text, filename=str(CORE_FILE))
    records = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        base = re.sub(r"V\d+$", "", node.name)
        base_norm = normalize(base)
        marker = preceding_marker(lines, node.lineno)
        exact = []
        for row in queue:
            haystack = normalize(" ".join(str(v) for v in row.values()))
            if base_norm and base_norm in haystack:
                exact.append(row["edge_id"])
        if marker:
            marker_ids = re.findall(r"(?:RX|RH)-\d{3}", marker)
            exact.extend(edge for edge in marker_ids if any(r["edge_id"] == edge for r in queue))
        exact = list(dict.fromkeys(exact))
        edge_rows = []
        for edge in exact:
            qrow = next(r for r in queue if r["edge_id"] == edge)
            vrow = rescore.get(edge, {})
            edge_rows.append(
                {
                    "edge_id": edge,
                    "members": qrow.get("members"),
                    "status": qrow.get("status"),
                    "value_action": vrow.get("value_action"),
                    "product_form": vrow.get("product_form"),
                    "validated_value_0_100": vrow.get("validated_value_0_100"),
                    "surfaces": qrow.get("downstream_product_surfaces"),
                }
            )
        records.append(
            {
                "kernel_id": f"LCB-K{len(records)+1:03d}",
                "class_name": node.name,
                "base_name": base,
                "source_line": node.lineno,
                "source_marker": marker,
                "docstring": ast.get_docstring(node),
                "public_methods": [m for m in methods if not m.startswith("_")],
                "all_methods": methods,
                "queue_matches": edge_rows,
                "origin": "r49_executable_library",
                "adoption_state": "IMPORTED_UNDER_CORE_V2_REVIEW",
            }
        )
    return records


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    all_files = sorted(p for p in SOURCE.rglob("*") if p.is_file())
    extension_counts = Counter(p.suffix.lower() or "[none]" for p in all_files)
    extension_bytes = Counter()
    python_errors = []
    tsv_profiles = []
    markdown_profiles = []
    hashes = {}

    # This loop intentionally reads every file in full. It is both a package audit and
    # a guard against silently ignoring large historical registries/results.
    for path in all_files:
        rel = path.relative_to(SOURCE).as_posix()
        raw = path.read_bytes()
        hashes[rel] = hashlib.sha256(raw).hexdigest()
        extension_bytes[path.suffix.lower() or "[none]"] += len(raw)
        if path.suffix.lower() == ".py":
            try:
                ast.parse(raw.decode("utf-8-sig"), filename=rel)
            except Exception as exc:  # pragma: no cover - audit path
                python_errors.append({"file": rel, "error": repr(exc)})
        elif path.suffix.lower() == ".tsv":
            text = raw.decode("utf-8-sig")
            line_count = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
            header = text.splitlines()[0].split("\t") if text.splitlines() else []
            tsv_profiles.append(
                {"file": rel, "bytes": len(raw), "lines": line_count, "columns": header}
            )
        elif path.suffix.lower() == ".md":
            text = raw.decode("utf-8-sig")
            headings = [line.strip() for line in text.splitlines() if line.startswith("#")]
            verdicts = re.findall(r"(?im)^.*verdict.*$", text)
            markdown_profiles.append(
                {"file": rel, "bytes": len(raw), "headings": headings, "verdict_lines": verdicts}
            )

    queue = read_tsv(QUEUE_FILE)
    rescore_rows = read_tsv(RESCORE_FILE)
    rescore = {row["edge_id"]: row for row in rescore_rows}
    cores = class_registry(queue, rescore)

    audit = {
        "source_root": str(SOURCE),
        "files_read_fully": len(all_files),
        "bytes_read": sum(p.stat().st_size for p in all_files),
        "extension_counts": dict(extension_counts),
        "extension_bytes": dict(extension_bytes),
        "python_parse_errors": python_errors,
        "latest_queue_rows": len(queue),
        "latest_rescore_rows": len(rescore_rows),
        "executable_classes": len(cores),
        "class_queue_exact_match_count": sum(bool(r["queue_matches"]) for r in cores),
        "status_counts": dict(Counter(r.get("status", "") for r in queue)),
        "value_action_counts": dict(Counter(r.get("value_action", "") for r in rescore_rows)),
        "sha256": hashes,
    }
    (OUT / "source_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "core_registry_raw.json").write_text(
        json.dumps(cores, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "tsv_profiles.json").write_text(
        json.dumps(tsv_profiles, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "markdown_profiles.json").write_text(
        json.dumps(markdown_profiles, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps({k: audit[k] for k in audit if k != "sha256"}, indent=2))


if __name__ == "__main__":
    main()
