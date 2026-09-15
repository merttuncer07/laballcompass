from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "01_V2_CORE"


def lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    registry = lines(CORE / "generated_v2_foundry" / "CORE_V2_FOUNDRY_UNIFIED_REGISTRY.jsonl")
    counts: dict[str, int] = {}
    for row in registry:
        counts[row["family"]] = counts.get(row["family"], 0) + 1

    parent_tests = list((ROOT / "02_FOUNDRY_ALL_PRODUCTS" / "parent_products").rglob("test_*.py"))
    product_dirs = [p for p in (ROOT / "02_FOUNDRY_ALL_PRODUCTS" / "products").iterdir() if p.is_dir() and p.name.startswith("P")]

    # R388 integrity rule: physical V2 executable coverage is authority-aware rather
    # than a weak `>= 1` existence check. Only directories with both composition
    # metadata and at least one direct test surface count as executable suites.
    v2_dirs = sorted(
        p for p in (CORE / "products").iterdir()
        if p.is_dir() and p.name.startswith("V2P") and (p / "COMPOSITION.json").exists() and list(p.glob("test_*.py"))
    )
    v2_ids = [p.name.split("_", 1)[0] for p in v2_dirs]

    authority = load(CORE / "CURRENT_PRODUCT_AUTHORITY.json")
    foundry_counts = load(CORE / "generated_v2_foundry" / "CORE_V2_FOUNDRY_COUNTS.json")
    queue = load(CORE / "generated_v2_foundry" / "CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json")
    universe_path = CORE / "generated_v2_foundry" / "CORE_V2_FOUNDRY_CANDIDATE_UNIVERSE.jsonl"
    universe = lines(universe_path)

    expected = {"LCB_KERNEL": 96, "FOUNDRY_PARENT": 69, "FOUNDRY_PRODUCT": 145}
    assert len(registry) == 310, len(registry)
    assert counts == expected, counts
    assert len(parent_tests) == 69, len(parent_tests)
    assert len(product_dirs) == 145, len(product_dirs)

    assert authority["status"] == "PROMOTED_CANONICAL_PRODUCT_AUTHORITY", authority["status"]
    assert authority["registry_family_count"] == 455 and authority["registry455_unchanged"]
    assert len(v2_dirs) == authority["canonical_executable_suite_count"], (len(v2_dirs), authority["canonical_executable_suite_count"])
    assert v2_ids == authority["canonical_executable_suite_ids"], "physical V2 suite IDs drift from current authority"
    assert set(authority.get("quarantined_product_ids", [])).isdisjoint(v2_ids), "quarantined product present in canonical physical V2 suite set"

    assert len(universe) == foundry_counts["candidate_universe_rows"], (len(universe), foundry_counts["candidate_universe_rows"])
    assert sum(bool(r.get("active_for_build", True)) for r in universe) == foundry_counts["active_candidate_rows"]
    assert len(queue) == foundry_counts["queue_rows"] == 1000
    assert foundry_counts["queue_completed_suite_rows"] == authority["canonical_executable_suite_count"]

    assert (ROOT / "03_LCB_EXECUTABLE_AND_EVIDENCE" / "prototypes").is_dir()
    result = {
        "base_registry_records": len(registry),
        "family_counts": counts,
        "foundry_parent_test_files": len(parent_tests),
        "foundry_product_directories": len(product_dirs),
        "canonical_product_authority_release": authority["authority_release"],
        "canonical_v2_executable_suites": len(v2_dirs),
        "canonical_v2_distinct_families": authority["canonical_distinct_family_count"],
        "quarantined_product_ids": authority.get("quarantined_product_ids", []),
        "full_candidate_universe_rows": len(universe),
        "active_candidate_universe_rows": foundry_counts["active_candidate_rows"],
        "operational_queue_rows": len(queue),
        "total_addressable_artifacts_including_v2_composites": len(registry) + len(v2_dirs),
        "status": "INVENTORY_COMPLETE_AUTHORITY_ALIGNED",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
