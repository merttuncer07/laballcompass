from __future__ import annotations

import ast
import csv
import json
import re
from collections import Counter
from pathlib import Path


WORKSPACE = Path(r"C:\Users\mertt\OneDrive\Belgeler\ChatGPT\newlabexplore")
LAB = WORKSPACE / "LABALLCOMPASS_R399_REHYDRATED_LAB_2026-08-30"
CORE = LAB / "R392_EXACT_BASE" / "01_V2_CORE"
PRODUCTS = CORE / "products"
HERE = Path(__file__).resolve().parent
OUTPUT_JSON = HERE / "R401_PRODUCT_MATERIALITY_MATRIX.json"
OUTPUT_TSV = HERE / "R401_PRODUCT_MATERIALITY_MATRIX.tsv"


DOMAIN_TERMS = {
    "allocation": ("allocation", "budget", "portfolio", "resource"),
    "measurement": ("measurement", "sensor", "channel", "acquisition", "observability"),
    "decision": ("decision", "regret", "action", "policy"),
    "robustness": ("robust", "stress", "uncertainty", "sensitivity", "tipping"),
    "safety": ("safe", "constraint", "viability", "fail closed", "coverage"),
    "compression": ("compression", "representation", "merge", "reduction"),
    "memory": ("memory", "eviction", "retention", "deletion"),
    "calibration": ("calibration", "interval", "coverage", "confidence"),
    "systems": ("dynamical", "control", "stability", "state", "model"),
    "finance": ("asset", "return", "hedge", "portfolio", "trading"),
}


def first_paragraph(path: Path) -> str:
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("**") and stripped.endswith("**"):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if stripped.startswith(("- ", "|", "```")):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))
    return next((p for p in paragraphs if len(p) >= 35), paragraphs[0] if paragraphs else "")


def python_facts(product_dir: Path) -> dict:
    public_functions = []
    public_classes = []
    imports = set()
    test_methods = 0
    source_lines = 0
    parse_errors = []
    for path in sorted(product_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        source_lines += text.count("\n") + 1
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            parse_errors.append({"file": path.name, "error": str(exc)})
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif node.module:
                    imports.add(node.module.split(".")[0])
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    test_methods += 1
                elif not node.name.startswith("_") and not path.name.startswith("test_"):
                    public_functions.append(node.name)
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_") and not path.name.startswith("test_"):
                public_classes.append(node.name)
    return {
        "public_functions": sorted(set(public_functions)),
        "public_classes": sorted(set(public_classes)),
        "imports": sorted(imports - {"__future__"}),
        "test_methods": test_methods,
        "source_lines": source_lines,
        "parse_errors": parse_errors,
    }


def main() -> None:
    authority = json.loads((CORE / "CURRENT_PRODUCT_AUTHORITY.json").read_text(encoding="utf-8"))
    canonical = set(authority["canonical_executable_suite_ids"])
    distinct_ids = set(authority["canonical_distinct_family_ids"])
    rows = []
    for product_dir in sorted(PRODUCTS.glob("V2P*")):
        match = re.match(r"(V2P\d{3})_(.+)", product_dir.name)
        if not match:
            continue
        product_id, short_name = match.groups()
        composition_path = product_dir / "COMPOSITION.json"
        composition = json.loads(composition_path.read_text(encoding="utf-8")) if composition_path.exists() else {}
        readme = first_paragraph(product_dir / "README.md")
        result = first_paragraph(product_dir / "PRODUCT_RESULT.md")
        combined = f"{readme} {result} {json.dumps(composition, ensure_ascii=False)}".lower()
        facts = python_facts(product_dir)
        domains = [domain for domain, terms in DOMAIN_TERMS.items() if any(term in combined for term in terms)]
        evidence_markers = {
            "mentions_real_data": bool(re.search(r"\breal[- ](?:data|world|market)|empirical", combined)),
            "mentions_synthetic": bool(re.search(r"synthetic|toy|deterministic", combined)),
            "mentions_failure_region": bool(re.search(r"failure|can hurt|losing|fail[- ]closed", combined)),
            "mentions_collapse": "collapse" in combined,
            "mentions_comparator": bool(re.search(r"comparator|removal control|baseline|ablation", combined)),
        }
        third_party = sorted(set(facts["imports"]) & {"numpy", "scipy", "sklearn", "pandas", "networkx"})
        has_clear_api = bool(facts["public_functions"] or facts["public_classes"])
        canonical_status = "CANONICAL" if product_id in canonical else ("QUARANTINED" if product_id == "V2P047" else "NONCANONICAL")
        family_status = "DISTINCT_FAMILY" if product_id in distinct_ids else "FAMILY_VARIANT_OR_QUARANTINED"
        practical_signals = sum(
            (
                has_clear_api,
                facts["test_methods"] >= 6,
                bool(domains),
                evidence_markers["mentions_comparator"],
                evidence_markers["mentions_failure_region"],
                not facts["parse_errors"],
            )
        )
        rows.append(
            {
                "product_id": product_id,
                "short_name": short_name,
                "canonical_status": canonical_status,
                "family_status": family_status,
                "supplier_id": composition.get("supplier_id"),
                "consumer_id": composition.get("consumer_id"),
                "operator": composition.get("operator") or composition.get("mechanism"),
                "readme_summary": readme,
                "result_summary": result,
                "domains": domains,
                "public_functions": facts["public_functions"],
                "public_classes": facts["public_classes"],
                "imports": facts["imports"],
                "third_party_dependencies": third_party,
                "test_methods": facts["test_methods"],
                "source_lines": facts["source_lines"],
                "evidence_markers": evidence_markers,
                "practical_signal_count": practical_signals,
                "parse_errors": facts["parse_errors"],
            }
        )

    payload = {
        "model_version": "R401_PRODUCT_MATERIALITY_MATRIX_V1",
        "authority_release": authority["authority_release"],
        "rows": rows,
        "counts": {
            "physical_product_directories": len(rows),
            "canonical_suites": sum(row["canonical_status"] == "CANONICAL" for row in rows),
            "quarantined": sum(row["canonical_status"] == "QUARANTINED" for row in rows),
            "direct_distinct_product_ids": sum(row["family_status"] == "DISTINCT_FAMILY" for row in rows),
            "total_test_methods": sum(row["test_methods"] for row in rows),
            "domain_counts": dict(Counter(domain for row in rows for domain in row["domains"]).most_common()),
        },
        "interpretation_boundary": "The matrix reports executable/API/evidence signals from current files. Material usefulness still requires human product-level adjudication and is not inferred from the signal count alone.",
    }
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    with OUTPUT_TSV.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "product_id", "short_name", "canonical_status", "family_status", "supplier_id", "consumer_id",
            "domains", "test_methods", "source_lines", "public_api", "third_party_dependencies", "readme_summary",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "product_id": row["product_id"],
                    "short_name": row["short_name"],
                    "canonical_status": row["canonical_status"],
                    "family_status": row["family_status"],
                    "supplier_id": row["supplier_id"],
                    "consumer_id": row["consumer_id"],
                    "domains": ",".join(row["domains"]),
                    "test_methods": row["test_methods"],
                    "source_lines": row["source_lines"],
                    "public_api": ",".join(row["public_classes"] + row["public_functions"]),
                    "third_party_dependencies": ",".join(row["third_party_dependencies"]),
                    "readme_summary": row["readme_summary"],
                }
            )
    print(json.dumps(payload["counts"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
