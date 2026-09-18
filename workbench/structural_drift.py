"""Compact, deterministic structural observations for a workbook revision."""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path

from openpyxl.utils.cell import column_index_from_string, coordinate_from_string


def _strong_block(block):
    fraction = block.get("match_fraction") or 0.0
    if block.get("kind") == "row_alignment":
        return (fraction >= 0.9 and block.get("matching_rows", 0) >= 3
                and len(block.get("column_mapping", [])) >= 2)
    return (fraction >= 0.9 and block.get("matching_cells", 0) >= 12
            and block.get("compared_positions", 0) >= 12)


def _sheet_correspondence(exact, structural):
    removed = list(exact.get("unmatched_sheets", {}).get("left", []))
    added = list(exact.get("unmatched_sheets", {}).get("right", []))
    candidates = []
    if structural:
        for block in structural.get("blocks", []):
            left, right = block["left"]["sheet"], block["right"]["sheet"]
            if left in removed and right in added and _strong_block(block):
                candidates.append({
                    "left_sheet": left, "right_sheet": right,
                    "kind": block.get("kind"),
                    "matching_cells": block.get("matching_cells", 0),
                    "matching_rows": block.get("matching_rows"),
                    "match_fraction": round(block.get("match_fraction") or 0.0, 6),
                })
    best_by_pair = {}
    for row in candidates:
        key = row["left_sheet"], row["right_sheet"]
        current = best_by_pair.get(key)
        if current is None or row["matching_cells"] > current["matching_cells"]:
            best_by_pair[key] = row
    candidates = list(best_by_pair.values())
    by_left, by_right = defaultdict(list), defaultdict(list)
    for row in candidates:
        by_left[row["left_sheet"]].append(row); by_right[row["right_sheet"]].append(row)
    accepted, withheld = [], []
    for row in candidates:
        left_options = sorted(by_left[row["left_sheet"]], key=lambda x: -x["matching_cells"])
        right_options = sorted(by_right[row["right_sheet"]], key=lambda x: -x["matching_cells"])
        unique = len(left_options) == 1 and len(right_options) == 1
        if unique:
            accepted.append(row)
        else:
            withheld.append({
                "left_sheet": row["left_sheet"], "right_sheet": row["right_sheet"],
                "reason": "Multiple strong structural correspondences; rename identity withheld.",
            })
    return {
        "sheets_added": added,
        "sheets_removed": removed,
        "likely_sheet_renames": accepted,
        "rename_candidates_withheld": withheld,
        "correspondence_available": structural is not None,
        "interpretation": (
            "Rename candidates require one mutually unique, strong observed content/record correspondence."
            if structural else
            "Structural correspondence was not available; rename identity was not inferred."),
    }


def _header_observation(block, left_column, right_column):
    rows = block.get("row_mapping", [])
    if not rows:
        return None
    first = min(rows, key=lambda row: (row["left"], row["right"]))
    if first["left"] > 5 or first["right"] > 5:
        return None
    for cell in block.get("cells", []):
        left_col, left_row = coordinate_from_string(cell["left"])
        right_col, right_row = coordinate_from_string(cell["right"])
        if (left_col == left_column and right_col == right_column
                and left_row == first["left"] and right_row == first["right"]):
            left_value, right_value = cell.get("left_value"), cell.get("right_value")
            if (isinstance(left_value, str) and isinstance(right_value, str)
                    and left_value.strip() and right_value.strip()
                    and left_value.strip() != right_value.strip()):
                return {"before": left_value, "after": right_value,
                        "left_column": left_column, "right_column": right_column,
                        "basis": "Different text values in the first mapped row of a strong record correspondence."}
    return None


def _record_structure(structural):
    if not structural:
        return {
            "correspondence_available": False, "regions": [],
            "columns_added": [], "columns_removed": [], "columns_reordered": [],
            "likely_column_renames": [], "column_mapping_withheld": [],
            "interpretation": "Record/column correspondence was not available; column identity was not inferred.",
        }
    regions, added, removed, reordered, renames, withheld = [], [], [], [], [], []
    for block in structural.get("blocks", []):
        if block.get("kind") != "row_alignment":
            continue
        strong = _strong_block(block)
        mapping = block.get("column_mapping", [])
        row_mapping = block.get("row_mapping", [])
        left_total = len(row_mapping) + len(block.get("unmapped_left_rows", []))
        right_total = len(row_mapping) + len(block.get("unmapped_right_rows", []))
        region = {
            "left_sheet": block["left"]["sheet"], "right_sheet": block["right"]["sheet"],
            "strong_correspondence": strong,
            "matched_record_count": block.get("matching_rows", 0),
            "left_matched_record_rate": round(len(row_mapping) / left_total, 6) if left_total else None,
            "right_matched_record_rate": round(len(row_mapping) / right_total, 6) if right_total else None,
            "ambiguous_or_unmatched_left_records": len(block.get("unmapped_left_rows", [])),
            "ambiguous_or_unmatched_right_records": len(block.get("unmapped_right_rows", [])),
            "different_or_uncompared_cells": block.get("different_or_uncompared_cells", 0),
            "pure_row_reorder": (bool(row_mapping)
                                 and any(row["left"] != row["right"] for row in row_mapping)
                                 and block.get("different_or_uncompared_cells", 0) == 0),
        }
        regions.append(region)
        if not strong:
            withheld.append({"left_sheet": block["left"]["sheet"],
                             "right_sheet": block["right"]["sheet"],
                             "reason": "Record correspondence did not meet the strong deterministic threshold."})
            continue
        for column in block.get("unmapped_right_columns", []):
            added.append({"sheet": block["right"]["sheet"], "column": column,
                          "basis": "Unmapped populated column in a strong record correspondence."})
        for column in block.get("unmapped_left_columns", []):
            removed.append({"sheet": block["left"]["sheet"], "column": column,
                            "basis": "Unmapped populated column in a strong record correspondence."})
        right_positions = [column_index_from_string(row["right"]) for row in mapping]
        if right_positions != sorted(right_positions):
            reordered.append({"left_sheet": block["left"]["sheet"],
                              "right_sheet": block["right"]["sheet"],
                              "mapping": mapping})
        for pair in mapping:
            observation = _header_observation(block, pair["left"], pair["right"])
            if observation:
                renames.append({"sheet": block["left"]["sheet"], **observation})
    ambiguous = (structural.get("record_alignment", {}).get("ambiguous_rows_omitted", 0))
    if ambiguous:
        withheld.append({"reason": f"{ambiguous} ambiguous record candidate(s) were omitted by the matcher."})
    return {
        "correspondence_available": True,
        "regions": regions,
        "columns_added": added,
        "columns_removed": removed,
        "columns_reordered": reordered,
        "likely_column_renames": renames,
        "column_mapping_withheld": withheld,
        "interpretation": (
            "Added/removed labels mean unmatched populated columns inside a strong observed record correspondence; "
            "they do not assign business semantics."),
    }


def _formula_structure(triage):
    fields = {
        "formula_logic_changes": ("formula_logic_change", None),
        "formula_to_literal": ("formula_to_literal", None),
        "literal_to_formula": ("literal_to_formula", None),
        "formulas_introduced": ("added_content", "formula_introduced"),
        "formulas_removed": ("removed_content", "formula_removed"),
    }
    result = {}
    for name, (category, transition) in fields.items():
        groups = [row for row in triage.get("groups", [])
                  if row["category"] == category
                  and (transition is None or row.get("formula_transition") == transition)]
        result[name] = {
            "group_count": len(groups),
            "changed_cell_count": sum(row["changed_cell_count"] for row in groups),
            "triage_group_ids": [row["id"] for row in groups],
        }
    return result


def _external_summary(exact):
    observed = exact.get("external_dependencies", {})
    names = [row["name"] for row in exact.get("input_files", [])]
    left_name = names[0] if names else None
    right_name = names[1] if len(names) > 1 else None
    references = observed.get("references", [])
    before = [row for row in references if row.get("from_workbook") == left_name]
    after = [row for row in references if row.get("from_workbook") == right_name]

    def identity(row):
        if row.get("identity_basis") == "Before/after identity cannot be established safely":
            return None
        return str(row.get("reference", "")).casefold()

    left_ids = {identity(row) for row in before if identity(row)}
    right_ids = {identity(row) for row in after if identity(row)}
    return {
        "parser_available": observed.get("parser_available", False),
        "before_references": before,
        "after_references": after,
        "introduced": sorted(right_ids - left_ids),
        "removed": sorted(left_ids - right_ids),
        "resolved_against_supplied_evidence": [row for row in references
                                                if row.get("status") == "resolved_against_supplied_evidence"],
        "unresolved_or_missing": [row for row in references
                                  if row.get("status") == "unresolved_or_missing"],
        "identity_ambiguous": [row for row in references if identity(row) is None],
        "limitations": observed.get("limitations", [
            "External-reference observations were unavailable from the existing parser output."]),
    }


def build_structural_drift(exact, triage, structural=None):
    """Build a compact summary without changing Revision Triage."""
    return {
        "schema_version": 1,
        "method": "structural_drift_snapshot_v1",
        "input_files": exact.get("input_files", []),
        "workbook_structure": _sheet_correspondence(exact, structural),
        "record_structure": _record_structure(structural),
        "formula_structure": _formula_structure(triage),
        "external_dependencies": _external_summary(exact),
        "analysis_coverage": triage.get("dependency_coverage", exact.get("dependency_coverage", {})),
        "scope": [
            "This snapshot summarizes observed structure; it does not assign audit risk, materiality or required work.",
            "Rename and column identity are withheld when existing deterministic correspondence is absent or ambiguous.",
            "Unresolved dependency coverage means the supported graph is incomplete, not that a workbook is broken.",
        ],
    }


def write_structural_drift(exact_path, triage_path, destination, structural_path=None):
    exact = json.loads(Path(exact_path).read_text(encoding="utf-8"))
    triage = json.loads(Path(triage_path).read_text(encoding="utf-8"))
    structural = (json.loads(Path(structural_path).read_text(encoding="utf-8"))
                  if structural_path and Path(structural_path).is_file() else None)
    result = build_structural_drift(exact, triage, structural)
    destination = Path(destination)
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    return destination
