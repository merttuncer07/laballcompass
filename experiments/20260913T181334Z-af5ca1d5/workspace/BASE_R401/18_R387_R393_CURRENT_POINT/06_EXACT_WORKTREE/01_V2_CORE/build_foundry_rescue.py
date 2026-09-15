from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
OUTER = WORKSPACE / "INPUT_PRODUCT_FOUNDRY_P134_2026-08-25" / "HANDOFF_LABALLCOMPASS_PRODUCT_FOUNDRY_P134_2026-08-25"
BASE = WORKSPACE / "INPUT_PRODUCT_FOUNDRY_BASE_P007_2026-08-25" / "LABALLCOMPASS_PRODUCT_INTERACTION_FOUNDRY_WORK"
GENERATED = WORKSPACE / "lcb_core_revision" / "generated"
RESCUE = WORKSPACE / "FOUNDRY_RESCUE_2026-08-25"
ZIP_PATH = WORKSPACE / "LABALLCOMPASS_FOUNDRY_SOURCE_RESCUE_2026-08-25.zip"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_tree(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise FileNotFoundError(source)
    shutil.copytree(source, destination)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def product_number(product_id: str) -> int:
    return int(product_id[1:])


def product_dirs() -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {}
    for root in (BASE / "03_OUTPUT" / "PRODUCTS", OUTER / "CURRENT_DELTA" / "03_OUTPUT" / "PRODUCTS"):
        if not root.is_dir():
            continue
        for path in root.iterdir():
            match = re.match(r"^(P\d{3})(?:_|$)", path.name)
            if path.is_dir() and match:
                found.setdefault(match.group(1), []).append(path)
    return found


def available_names() -> dict[str, str]:
    names: dict[str, str] = {}
    path = OUTER / "AVAILABLE_PRODUCT_ARTIFACTS.txt"
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^(P\d{3})_(.+)$", line.strip())
        if match:
            names[match.group(1)] = match.group(2)
    return names


def result_catalog() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    path = GENERATED / "FOUNDRY_PRODUCT_CATALOG.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["product_id"]] = row
    return rows


def make_product_index() -> list[dict[str, str]]:
    catalog = result_catalog()
    names = available_names()
    dirs = product_dirs()
    rows: list[dict[str, str]] = []
    for number in range(1, 135):
        product_id = f"P{number:03d}"
        record = catalog.get(product_id, {})
        paths = dirs.get(product_id, [])
        py_files = sorted({p.name for d in paths for p in d.rglob("*.py") if "__pycache__" not in p.parts})
        test_files = sorted({p.name for d in paths for p in d.rglob("test_*.py")})
        result_files = sorted({p.name for d in paths for p in d.rglob("PRODUCT_RESULT.md")})
        benchmark_files = sorted({p.name for d in paths for p in d.rglob("*.json")})

        if py_files and test_files:
            status = "FULL_SOURCE_AND_TEST"
        elif py_files:
            status = "PARTIAL_SOURCE_NO_TEST"
        elif result_files or record:
            status = "RESULT_ONLY_RECONSTRUCTION_REQUIRED"
        elif benchmark_files:
            status = "BENCHMARK_ONLY_RECONSTRUCTION_REQUIRED"
        else:
            status = "HISTORICAL_GAP_NO_MATERIALIZED_ARTIFACT"

        short_name = record.get("short_name") or names.get(product_id, "")
        if not short_name and paths:
            short_name = paths[0].name.split("_", 1)[1] if "_" in paths[0].name else ""

        rows.append(
            {
                "product_id": product_id,
                "short_name": short_name,
                "salvage_status": status,
                "parents": record.get("parents_raw", ""),
                "promotion_state_claim": record.get("promotion_state", ""),
                "source_files": ";".join(py_files),
                "test_files": ";".join(test_files),
                "result_present": "yes" if (result_files or record) else "no",
                "benchmark_files": ";".join(benchmark_files),
                "strength_salvaged": "yes" if record.get("strength_raw") else "no",
                "weakness_salvaged": "yes" if record.get("weakness_raw") else "no",
                "artifact_paths": ";".join(str(p.relative_to(WORKSPACE)).replace("\\", "/") for p in paths),
                "reconstruction_rule": (
                    "verify supplied source/tests; do not recreate"
                    if status == "FULL_SOURCE_AND_TEST"
                    else "rebuild from parent contracts, result evidence, strengths, weaknesses, and benchmarks; new code is a reconstruction, not byte-identical recovery"
                    if status != "HISTORICAL_GAP_NO_MATERIALIZED_ARTIFACT"
                    else "recover parent mapping from another archive/chat before implementation; do not invent historical identity"
                ),
            }
        )
    return rows


def make_parent_index() -> list[dict[str, str]]:
    registry = read_json(GENERATED / "FOUNDRY_PARENT_INTERFACE_REGISTRY.json")
    rows: list[dict[str, str]] = []
    for record in registry:
        source_files = [module["file"] for module in record.get("source_modules", [])]
        test_files = [test["file"] for test in record.get("test_files", [])]
        rows.append(
            {
                "parent_id": record["product_dir"],
                "kind": record["product_kind"],
                "relative_path": record["relative_path"],
                "source_files": ";".join(source_files),
                "test_files": ";".join(test_files),
                "test_method_count": str(record.get("test_method_count", 0)),
                "tested_public_callables": ";".join(record.get("tested_public_callables", [])),
                "capability_summary": record.get("readme_summary", "").replace("\n", " "),
            }
        )
    return rows


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_readme(product_rows: list[dict[str, str]], parent_rows: list[dict[str, str]], audit: dict) -> None:
    counts: dict[str, int] = {}
    for row in product_rows:
        counts[row["salvage_status"]] = counts.get(row["salvage_status"], 0) + 1
    full_ids = [row["product_id"] for row in product_rows if row["salvage_status"] == "FULL_SOURCE_AND_TEST"]
    partial_ids = [row["product_id"] for row in product_rows if row["salvage_status"] == "PARTIAL_SOURCE_NO_TEST"]
    benchmark_ids = [row["product_id"] for row in product_rows if row["salvage_status"] == "BENCHMARK_ONLY_RECONSTRUCTION_REQUIRED"]
    gap_ids = [row["product_id"] for row in product_rows if row["salvage_status"] == "HISTORICAL_GAP_NO_MATERIALIZED_ARTIFACT"]
    parents_mapped = sum(1 for row in product_rows if row["parents"])
    text = f"""# LABALLCOMPASS Product Foundry source rescue

This package preserves every supplied Foundry byte plus a conservative reconstruction index. It does not pretend that result prose is source code and does not recreate missing historical bytes.

## Definitive salvage state

- Parent products: **{len(parent_rows)}** complete code-derived interface records.
- Parent source/test archive: **209 Python files**, including **69 parent test files** and **271 represented parent tests**.
- Product IDs indexed: **134**.
- Full product source and tests: **{counts.get('FULL_SOURCE_AND_TEST', 0)}** — {', '.join(full_ids)}.
- Partial source without supplied tests: **{counts.get('PARTIAL_SOURCE_NO_TEST', 0)}** — {', '.join(partial_ids)}.
- Benchmark-only artifacts: **{counts.get('BENCHMARK_ONLY_RECONSTRUCTION_REQUIRED', 0)}** — {', '.join(benchmark_ids)}.
- Result/provenance records requiring reconstruction: **{counts.get('RESULT_ONLY_RECONSTRUCTION_REQUIRED', 0)}**.
- No materialized per-product artifact: **{counts.get('HISTORICAL_GAP_NO_MATERIALIZED_ARTIFACT', 0)}** — {', '.join(gap_ids)}.
- Product records with a salvaged parent mapping: **{parents_mapped}/134**.

## Important interpretation

The 69 parent products are not lost. Their source, tests, README capability descriptions, callable signatures, invariants, and tested public callables are preserved under `BASE_FOUNDATION_EXTRACTED/01_INPUTS` and indexed in `SALVAGE_INDEX/PARENT_SOURCE_INDEX.tsv`.

The historical cumulative claim of 134 products / 787 product tests is not reproducible from the supplied files as a whole. Only the products marked `FULL_SOURCE_AND_TEST` can be rerun directly from this rescue. A `PRODUCT_RESULT.md` is valuable reconstruction evidence, but it is not executable source.

For missing products, rebuild from the directed parent mapping, observed output, benchmark fixture, strengths, weaknesses, and interface contracts. Label that work as a reconstruction rather than claiming byte-identical recovery.

## Integrity observations

- Outer P134 handoff manifest: **{audit['outer_manifest']['matched']}/{audit['outer_manifest']['rows']} matched**.
- Extracted base manifest: **{audit['base_manifest']['matched']}/{audit['base_manifest']['rows']} matched**. The only observed mismatch is `03_OUTPUT/README.md`, consistent with a post-manifest edit/package defect; all original bytes are retained here.
- All supplied Python source parsed successfully in the prior audit.

## Navigation

- `SALVAGE_INDEX/PARENT_SOURCE_INDEX.tsv`: the 69 parent list with code paths, tests, callable contracts, and capability summaries.
- `SALVAGE_INDEX/PRODUCT_RECONSTRUCTION_INDEX.tsv`: P001–P134 status, parent mapping, source/test/result presence, and reconstruction rule.
- `SALVAGE_INDEX/FOUNDRY_PRODUCT_CATALOG.jsonl`: full recovered result evidence including strengths and weaknesses where present.
- `OUTER_HANDOFF_EXTRACTED`: exact supplied continuation package contents.
- `BASE_FOUNDATION_EXTRACTED`: exact extracted P001–P007 foundation, including parent source archive and full transcript.
- `SHA256SUMS.txt`: hashes for every rescue file except itself.
"""
    (RESCUE / "START_HERE.md").write_text(text, encoding="utf-8")


def build() -> None:
    if RESCUE.exists() or ZIP_PATH.exists():
        raise FileExistsError("Refusing to overwrite an existing rescue artifact")
    RESCUE.mkdir()
    copy_tree(OUTER, RESCUE / "OUTER_HANDOFF_EXTRACTED")
    copy_tree(BASE, RESCUE / "BASE_FOUNDATION_EXTRACTED")
    index_dir = RESCUE / "SALVAGE_INDEX"
    index_dir.mkdir()

    for name in (
        "FOUNDRY_PARENT_INTERFACE_REGISTRY.json",
        "FOUNDRY_PRODUCT_CATALOG.jsonl",
        "FOUNDRY_PRODUCT_CATALOG.tsv",
        "foundry_source_audit.json",
    ):
        shutil.copy2(GENERATED / name, index_dir / name)

    product_rows = make_product_index()
    parent_rows = make_parent_index()
    write_tsv(index_dir / "PRODUCT_RECONSTRUCTION_INDEX.tsv", product_rows)
    write_tsv(index_dir / "PARENT_SOURCE_INDEX.tsv", parent_rows)
    audit = read_json(GENERATED / "foundry_source_audit.json")
    write_readme(product_rows, parent_rows, audit)

    manifest = {
        "rescue_name": RESCUE.name,
        "parent_records": len(parent_rows),
        "product_records": len(product_rows),
        "product_status_counts": {
            status: sum(1 for row in product_rows if row["salvage_status"] == status)
            for status in sorted({row["salvage_status"] for row in product_rows})
        },
        "source_roots": [str(OUTER), str(BASE)],
        "interpretation": "salvage and reconstruction evidence; missing historical source is not silently invented",
    }
    (RESCUE / "RESCUE_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    hash_lines = []
    for path in sorted(p for p in RESCUE.rglob("*") if p.is_file()):
        rel = path.relative_to(RESCUE).as_posix()
        hash_lines.append(f"{sha256(path)}  {rel}")
    (RESCUE / "SHA256SUMS.txt").write_text("\n".join(hash_lines) + "\n", encoding="utf-8")

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in RESCUE.rglob("*") if p.is_file()):
            archive.write(path, (RESCUE.name / path.relative_to(RESCUE)).as_posix())
    (ZIP_PATH.with_suffix(ZIP_PATH.suffix + ".sha256")).write_text(
        f"{sha256(ZIP_PATH)}  {ZIP_PATH.name}\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    print(f"zip={ZIP_PATH}")
    print(f"zip_sha256={sha256(ZIP_PATH)}")


if __name__ == "__main__":
    build()
