from __future__ import annotations

import ast
import json
import re
from collections import Counter
from pathlib import Path


WORKSPACE = Path(r"C:\Users\mertt\OneDrive\Belgeler\ChatGPT\newlabexplore")
BASE = WORKSPACE / "LABALLCOMPASS_R399_REHYDRATED_LAB_2026-08-30" / "R392_EXACT_BASE"
PARENT_ROOT = BASE / "02_FOUNDRY_ALL_PRODUCTS" / "parent_products"
LCB_ROOT = BASE / "03_LCB_EXECUTABLE_AND_EVIDENCE"
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "R401_CAPABILITY_INVENTORY.json"

DOMAINS = {
    "allocation": ("allocation", "budget", "resource", "portfolio"),
    "measurement": ("measurement", "sensor", "channel", "information", "observ"),
    "decision": ("decision", "regret", "action", "policy"),
    "robustness": ("robust", "uncertainty", "sensitivity", "tipping", "stress"),
    "safety": ("safe", "constraint", "viability", "coverage", "certificate"),
    "compression": ("compression", "reduction", "merge", "representation"),
    "dynamics": ("dynamic", "control", "stability", "state", "system"),
    "causal_inference": ("causal", "intervention", "confound", "treatment"),
    "finance": ("portfolio", "asset", "return", "hedge", "mortgage", "trading"),
}


def prose(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    blocks = []
    for block in re.split(r"\n\s*\n", text):
        cleaned = " ".join(line.strip() for line in block.splitlines() if line.strip() and not line.lstrip().startswith(("#", "-", "|", "```")))
        if len(cleaned) >= 40:
            blocks.append(cleaned)
    return blocks[0] if blocks else ""


def ast_facts(paths: list[Path]) -> dict:
    classes = set()
    functions = set()
    imports = set()
    tests = 0
    lines = 0
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines += text.count("\n") + 1
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_") and not path.name.startswith("test_"):
                classes.add(node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    tests += 1
                elif not node.name.startswith("_") and not path.name.startswith(("test_", "demo_")):
                    functions.add(node.name)
            elif isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
    return {
        "public_classes": sorted(classes),
        "public_functions": sorted(functions),
        "imports": sorted(imports - {"__future__"}),
        "test_methods": tests,
        "source_lines": lines,
    }


def main() -> None:
    parents = []
    for tier in ("CURRENT_PRODUCTS", "RETRO_PRODUCTS"):
        for directory in sorted((PARENT_ROOT / tier).iterdir()):
            if not directory.is_dir():
                continue
            facts = ast_facts(list(directory.glob("*.py")))
            summary = prose(directory / "PRODUCT_RESULT.md") or prose(directory / "README.md")
            lower = summary.lower()
            domains = [name for name, terms in DOMAINS.items() if any(term in lower for term in terms)]
            parents.append(
                {
                    "capability_id": directory.name,
                    "tier": tier,
                    "summary": summary,
                    "domains": domains,
                    "has_demo": any(directory.glob("demo_*.py")),
                    "has_result": (directory / "PRODUCT_RESULT.md").exists(),
                    **facts,
                }
            )

    prototype_files = sorted((LCB_ROOT / "prototypes").glob("*PRODUCT_PROTOTYPES*.py"))
    latest = max(prototype_files, key=lambda path: path.stat().st_size)
    source = latest.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source)
    kernels = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        doc = ast.get_docstring(node) or ""
        methods = [child.name for child in node.body if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and not child.name.startswith("_")]
        kernels.append({"class_name": node.name, "docstring": doc, "public_methods": methods})

    payload = {
        "model_version": "R401_CAPABILITY_INVENTORY_V1",
        "parent_products": parents,
        "lcb_latest_prototype_file": str(latest.relative_to(BASE)),
        "lcb_executable_classes_parsed": len(kernels),
        "lcb_kernels": kernels,
        "counts": {
            "parent_products": len(parents),
            "current_parents": sum(row["tier"] == "CURRENT_PRODUCTS" for row in parents),
            "retro_parents": sum(row["tier"] == "RETRO_PRODUCTS" for row in parents),
            "parent_test_methods": sum(row["test_methods"] for row in parents),
            "parent_domain_counts": dict(Counter(domain for row in parents for domain in row["domains"]).most_common()),
            "lcb_classes_in_latest_consolidated_source": len(kernels),
        },
        "interpretation_boundary": "Parents are standalone executable products; LCB classes are reusable kernels. This inventory does not relabel either layer as a promoted V2 product.",
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["counts"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
