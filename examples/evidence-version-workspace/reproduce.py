#!/usr/bin/env python3
"""Reproduce the genuine many-file evidence-version workflow."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from workbench.evidence_workspace import (
    confirm_candidate,
    create_workspace,
    import_folder,
    workspace_state,
)


OFGEM = ROOT / "examples/published-version-review/ofgem-ed2-pcfm"
SONI = ROOT / "examples/soni-price-control/sources/soni-financial-model.xlsx"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    options = parser.parse_args(argv)
    output = Path(options.output).expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Output directory must be new or empty")
    output.mkdir(parents=True, exist_ok=True)
    incoming = output / "incoming"
    incoming.mkdir()
    workspace = output / "workspace"
    preserved = json.loads((OFGEM / "result.json").read_text())
    before_source = OFGEM / preserved["before"]["file"]
    after_source = OFGEM / preserved["after"]["file"]
    sources = (before_source, after_source, SONI)
    original_hashes = {str(path): sha(path) for path in sources}
    shutil.copyfile(before_source, incoming / "baseline-received.xlsx")
    shutil.copyfile(before_source, incoming / "same-file-from-email.xlsx")
    shutil.copyfile(after_source, incoming / "client-final-renamed.xlsx")
    shutil.copyfile(SONI, incoming / "unrelated-financial-model.xlsx")

    create_workspace(workspace, "Evidence Version Intelligence demo")
    imported = import_folder(workspace, incoming)
    state = workspace_state(workspace)
    before_id = next(blob["id"] for blob in state["file_blobs"]
                     if blob["sha256"] == preserved["before"]["sha256"])
    after_id = next(blob["id"] for blob in state["file_blobs"]
                    if blob["sha256"] == preserved["after"]["sha256"])
    candidate = next(candidate for candidate in state["candidates"]
                     if {candidate["left_blob_id"], candidate["right_blob_id"]} == {before_id, after_id})
    if candidate["classification"] != "likely_revision" or candidate["status"] != "pending":
        raise RuntimeError("The genuine Ofgem versions were not proposed for confirmation")
    confirmed = confirm_candidate(
        workspace, candidate["id"], before_id, artifact_name="Ofgem ED2 Price Control Financial Model"
    )
    content = json.loads(Path(confirmed["comparison_report"]).with_name("content.json").read_text())
    counts = {
        "same_value": sum(block["matching_cells"] for block in content["blocks"]),
        "same_formula": sum(block["matching_formula_cells"] for block in content["blocks"]),
        "changed_value": sum(sum(cell.get("comparison") == "changed_value" for cell in block["cells"])
                             for block in content["blocks"]),
        "changed_formula": sum(sum(cell.get("comparison") == "changed_formula" for cell in block["cells"])
                               for block in content["blocks"]),
        "added": sum(sum(cell.get("comparison") == "added" for cell in block["cells"])
                     for block in content["blocks"]),
        "removed": sum(sum(cell.get("comparison") == "removed" for cell in block["cells"])
                       for block in content["blocks"]),
        "uncompared": sum(block["uncompared_cells"] for block in content["blocks"]),
        "unique_potential_downstream_targets": len({target for block in content["blocks"]
                                                     for target in block.get("difference_formula_targets", [])}),
        "changed_blocks_with_impacts": sum(bool(block.get("difference_formula_targets"))
                                           for block in content["blocks"]),
    }
    expected = preserved["comparison"]
    for key, value in counts.items():
        if value != expected[key]:
            raise RuntimeError(f"Ofgem count changed for {key}: {value} != {expected[key]}")
    final_state = workspace_state(workspace)
    triage_path = Path(confirmed["comparison_report"]).parents[1] / "triage" / "triage.json"
    triage = json.loads(triage_path.read_text())
    result = {
        "schema_version": final_state["schema_version"],
        "import": imported,
        "ofgem_candidate": candidate,
        "confirmation": confirmed,
        "artifact_history": final_state["artifacts"],
        "comparison_counts": counts,
        "revision_triage": {
            "report": str(triage_path.with_name("index.html")),
            "summary": triage["summary"],
            "group_type_distribution": triage["group_type_distribution"],
            "structural_reach": triage["structural_reach"],
            "dependency_coverage": triage["dependency_coverage"],
        },
        "preserved_counts_match": True,
        "original_files_unchanged": original_hashes == {str(path): sha(path) for path in sources},
    }
    (output / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(output / "result.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
