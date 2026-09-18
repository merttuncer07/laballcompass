"""Persistent local evidence identity and version workspaces.

File blobs represent exact bytes. Evidence versions exist only inside one logical
artifact. Workbook cell/formula dependencies remain in the existing workbench.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import uuid

from .content import compare_content, formula_descriptor
from .evidence_schema import (SCHEMA_VERSION, blob_id as make_blob_id,
                              candidate_id as make_candidate_id,
                              create_schema_v2, migrate_v1_to_v2)
from .cli import save_workbook_analysis
from .workbooks import open_workbooks


DATABASE_NAME = "workspace.sqlite3"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _load_json(value):
    return json.loads(value) if value else {}


def _workspace_path(path):
    return Path(path).expanduser().resolve()


def _require_reason(reason):
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("A correction reason is required")
    return reason.strip()


@contextmanager
def _connect(path):
    root = _workspace_path(path)
    database = root / DATABASE_NAME
    if not database.is_file():
        raise ValueError(f"Not an evidence workspace: {root}")
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version == 1:
        migrate_v1_to_v2(connection)
        version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version != SCHEMA_VERSION:
        connection.close()
        raise ValueError(f"Unsupported evidence workspace schema: {version}")
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def create_workspace(path, name=None):
    root = _workspace_path(path)
    root.mkdir(parents=True, exist_ok=True)
    database = root / DATABASE_NAME
    if database.exists():
        with _connect(root) as connection:
            row = connection.execute("SELECT id, name FROM workspace").fetchone()
            if row is None:
                raise ValueError("Workspace database is incomplete")
        from .workspace_report import write_workspace_report
        write_workspace_report(root)
        return {"workspace": str(root), "id": row["id"], "name": row["name"],
                "schema_version": SCHEMA_VERSION, "created": False}
    if any(root.iterdir()):
        raise ValueError("A new workspace folder must be empty")
    (root / "objects").mkdir()
    (root / "comparisons").mkdir()
    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        create_schema_v2(connection)
        wid = "ws_" + uuid.uuid4().hex[:16]
        connection.execute(
            "INSERT INTO workspace(id, name, created_at) VALUES (?, ?, ?)",
            (wid, name or root.name, _now()),
        )
        connection.commit()
    finally:
        connection.close()
    from .workspace_report import write_workspace_report
    write_workspace_report(root)
    return {"workspace": str(root), "id": wid, "name": name or root.name,
            "schema_version": SCHEMA_VERSION, "created": True}


def _fingerprint(workbook):
    sheets = []
    formula_hashes = set()
    total_populated = total_formulas = 0
    for sheet in workbook:
        populated = formulas = 0
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                populated += 1
                if cell.data_type == "f":
                    formulas += 1
                    description = formula_descriptor(cell)
                    if description is not None:
                        formula_hashes.add(hashlib.sha256(description.encode("utf-8")).hexdigest())
        total_populated += populated
        total_formulas += formulas
        sheets.append({"name": sheet.title, "max_row": sheet.max_row,
                       "max_column": sheet.max_column, "populated_cells": populated,
                       "formula_cells": formulas})
    return {"schema_version": 1, "sheet_names": [sheet["name"] for sheet in sheets],
            "sheets": sheets, "sheet_count": len(sheets),
            "populated_cells": total_populated, "formula_cells": total_formulas,
            "formula_hashes": sorted(formula_hashes)}


def _ratio(a, b):
    return min(a, b) / max(a, b) if max(a, b) else 1.0


def _candidate_evidence(left, right, left_name, right_name, paths, books):
    left_sheets = set(left["sheet_names"])
    right_sheets = set(right["sheet_names"])
    union = left_sheets | right_sheets
    sheet_overlap = len(left_sheets & right_sheets) / len(union) if union else 1.0
    populated_ratio = _ratio(left["populated_cells"], right["populated_cells"])
    formula_left = set(left["formula_hashes"])
    formula_right = set(right["formula_hashes"])
    formula_common = len(formula_left & formula_right)
    formula_overlap = (formula_common / min(len(formula_left), len(formula_right))
                       if min(len(formula_left), len(formula_right)) else 0.0)
    filename_similarity = SequenceMatcher(
        None, Path(left_name).stem.casefold(), Path(right_name).stem.casefold()).ratio()
    evidence = {
        "schema_version": 1,
        "structure": {"left_sheet_count": left["sheet_count"],
                      "right_sheet_count": right["sheet_count"],
                      "common_sheet_names": sorted(left_sheets & right_sheets),
                      "sheet_name_overlap": round(sheet_overlap, 6),
                      "populated_cell_count_ratio": round(populated_ratio, 6),
                      "common_formula_text_hashes": formula_common,
                      "formula_text_overlap_of_smaller_set": round(formula_overlap, 6)},
        "filename_similarity": round(filename_similarity, 6),
        "filename_role": "Explanatory only; filename similarity never establishes a version relationship.",
        "reasons": [],
        "cautions": ["Likely revision is a proposal, not confirmed provenance.",
                     "Similar content does not prove common origin."],
    }
    plausible_gate = ((sheet_overlap >= 0.5 and populated_ratio >= 0.4)
                      or (formula_common >= 3 and formula_overlap >= 0.4)
                      or (left["sheet_count"] == right["sheet_count"] and populated_ratio >= 0.8))
    if not plausible_gate:
        evidence["reasons"].append("Insufficient structural overlap to run the bounded content matcher.")
        return "no_confident_match", evidence
    same_layout = left_sheets == right_sheets and bool(left_sheets)
    try:
        result = compare_content(paths, books, same_layout=same_layout)
    except ValueError as error:
        evidence["reasons"].append("Candidate content assessment stopped at a safety limit: " + str(error))
        evidence["assessment_incomplete"] = True
        return "no_confident_match", evidence
    exact_supported = False
    if same_layout:
        compared = sum(block["compared_positions"] for block in result["blocks"])
        matching_values = sum(block["matching_cells"] for block in result["blocks"])
        matching_formulas = sum(block["matching_formula_cells"] for block in result["blocks"])
        changed = sum(block["changed_cells"] for block in result["blocks"])
        uncomparable = sum(block["uncompared_cells"] for block in result["blocks"])
        matching = matching_values + matching_formulas
        fraction = matching / compared if compared else 0.0
        evidence["same_layout"] = {"compared_positions": compared,
                                   "matching_literal_values": matching_values,
                                   "matching_formula_texts": matching_formulas,
                                   "changed_or_added_removed_positions": changed,
                                   "uncomparable_positions": uncomparable,
                                   "unchanged_fraction": round(fraction, 6)}
        exact_supported = ((compared >= 6 and matching >= 6 and fraction >= 0.8)
                           or (compared >= 20 and matching >= max(12, int(compared * 0.55)))
                           or (formula_common >= 3 and formula_overlap >= 0.6 and populated_ratio >= 0.5))
        if exact_supported:
            evidence["reasons"].append(
                f"Same named-sheet coordinates contain {matching} unchanged values/formulas across {compared} positions.")
            if fraction >= 0.8:
                return "likely_revision", evidence
        if compared and fraction < 0.8:
            try:
                result = compare_content(paths, books, same_layout=False)
            except ValueError as error:
                evidence["reasons"].append("General correspondence assessment stopped at a safety limit: " + str(error))
                evidence["assessment_incomplete"] = True
                return ("likely_revision" if exact_supported else "no_confident_match"), evidence
    blocks = result["blocks"]
    best = max(blocks, key=lambda block: (block.get("matching_cells", 0),
                                          block.get("match_fraction") or 0), default=None)
    if best is not None:
        best_matching = best.get("matching_cells", 0)
        best_fraction = best.get("match_fraction") or 0.0
        minimum = max(12, min(100, int(min(left["populated_cells"], right["populated_cells"]) * 0.05)))
        evidence["general_correspondence"] = {
            "kind": best.get("kind"), "matching_cells": best_matching,
            "compared_positions": best.get("compared_positions", 0),
            "match_fraction": round(best_fraction, 6),
            "minimum_matching_cells_required": minimum,
            "left": best.get("left"), "right": best.get("right"),
            "total_candidate_regions": result.get("total_blocks_found", len(blocks)),
            "ambiguous_rows_omitted": result.get("record_alignment", {}).get("ambiguous_rows_omitted", 0)}
        independent_structure = populated_ratio >= 0.5 and (
            sheet_overlap >= 0.5 or formula_common >= 3 or left["sheet_count"] == right["sheet_count"])
        if independent_structure and best_matching >= minimum and best_fraction >= 0.9:
            evidence["reasons"].append(
                f"The existing {best.get('kind')} matcher found {best_matching} matching cells at {best_fraction:.1%} agreement.")
            return "likely_revision", evidence
    if exact_supported:
        return "likely_revision", evidence
    evidence["reasons"].append("Existing content and record matchers did not reach the conservative proposal threshold.")
    return "no_confident_match", evidence


def _store_object(root, source, sha256, extension):
    relative = Path("objects") / f"{sha256}{extension.lower()}"
    destination = root / relative
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest() != sha256:
            raise ValueError("Workspace object hash mismatch")
        return relative.as_posix()
    temporary = destination.with_suffix(destination.suffix + ".tmp-" + uuid.uuid4().hex)
    shutil.copyfile(source, temporary)
    if hashlib.sha256(temporary.read_bytes()).hexdigest() != sha256:
        temporary.unlink(missing_ok=True)
        raise ValueError("Evidence changed while it was being ingested")
    temporary.replace(destination)
    return relative.as_posix()


def _blob_name(connection, blob):
    row = connection.execute(
        "SELECT observed_name FROM file_occurrences WHERE blob_id = ? ORDER BY first_seen_at, id LIMIT 1",
        (blob["id"],)).fetchone()
    return row["observed_name"] if row else blob["sha256"][:16] + blob["extension"]


def import_folder(workspace, folder):
    root = _workspace_path(workspace)
    source_root = Path(folder).expanduser().resolve()
    if not source_root.is_dir():
        raise ValueError("Import source must be a folder")
    paths = sorted((path for path in source_root.iterdir()
                    if path.is_file() and path.suffix.lower() in (".xlsx", ".xlsm")
                    and not path.name.startswith("~$")), key=lambda path: path.name.casefold())
    if not paths:
        raise ValueError("Folder contains no .xlsx or .xlsm files")
    if len(paths) > 20:
        raise ValueError("Supply at most 20 workbooks per import")
    before_hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    inventory = []
    new_blob_ids = []
    with open_workbooks(paths) as (loaded_paths, books):
        fingerprints = [_fingerprint(book) for book in books]
        with _connect(root) as connection:
            for path, book, fingerprint in zip(loaded_paths, books, fingerprints):
                sha256 = book._lab_input_sha256
                existing = connection.execute(
                    "SELECT id, object_path FROM file_blobs WHERE sha256 = ?", (sha256,)).fetchone()
                timestamp = _now()
                if existing:
                    bid = existing["id"]
                    stored = root / existing["object_path"]
                    if not stored.is_file() or hashlib.sha256(stored.read_bytes()).hexdigest() != sha256:
                        raise ValueError("Stored file blob is missing or failed hash verification")
                    classification = "exact_duplicate"
                    connection.execute("UPDATE file_blobs SET last_seen_at = ? WHERE id = ?", (timestamp, bid))
                else:
                    bid = make_blob_id(sha256)
                    object_path = _store_object(root, path, sha256, path.suffix)
                    connection.execute(
                        """INSERT INTO file_blobs
                           (id, sha256, extension, object_path, size_bytes, first_seen_at,
                            last_seen_at, fingerprint_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (bid, sha256, path.suffix.lower(), object_path, path.stat().st_size,
                         timestamp, timestamp, _json(fingerprint)))
                    new_blob_ids.append(bid)
                    classification = "new_blob"
                occurrence = connection.execute(
                    "SELECT id FROM file_occurrences WHERE blob_id = ? AND source_path = ?",
                    (bid, str(path))).fetchone()
                if occurrence:
                    connection.execute("UPDATE file_occurrences SET last_seen_at = ? WHERE id = ?",
                                       (timestamp, occurrence["id"]))
                else:
                    connection.execute(
                        """INSERT INTO file_occurrences
                           (blob_id, source_path, observed_name, first_seen_at, last_seen_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (bid, str(path), path.name, timestamp, timestamp))
                inventory.append({"path": str(path), "name": path.name, "blob_id": bid,
                                  "sha256": sha256, "classification": classification})
    proposed = no_match = 0
    with _connect(root) as connection:
        rows = connection.execute(
            "SELECT id, object_path, sha256, extension, fingerprint_json FROM file_blobs ORDER BY first_seen_at, id").fetchall()
        by_id = {row["id"]: row for row in rows}
        pairs = {tuple(sorted((new_id, other_id))) for new_id in new_blob_ids for other_id in by_id
                 if new_id != other_id}
        for left_id, right_id in sorted(pairs):
            if connection.execute(
                "SELECT 1 FROM candidates WHERE left_blob_id = ? AND right_blob_id = ?",
                (left_id, right_id)).fetchone():
                continue
            left_row, right_row = by_id[left_id], by_id[right_id]
            candidate_paths = [root / left_row["object_path"], root / right_row["object_path"]]
            with open_workbooks(candidate_paths, preserve_order=True) as (opened_paths, books):
                classification, evidence = _candidate_evidence(
                    _load_json(left_row["fingerprint_json"]), _load_json(right_row["fingerprint_json"]),
                    _blob_name(connection, left_row), _blob_name(connection, right_row), opened_paths, books)
            status = "pending" if classification == "likely_revision" else "observed"
            connection.execute(
                """INSERT INTO candidates
                   (id, left_blob_id, right_blob_id, classification, status,
                    evidence_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (make_candidate_id(left_id, right_id), left_id, right_id, classification,
                 status, _json(evidence), _now()))
            proposed += int(classification == "likely_revision")
            no_match += int(classification == "no_confident_match")
    after_hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    if before_hashes != after_hashes:
        raise RuntimeError("An original evidence file changed during import")
    from .workspace_report import write_workspace_report
    report = write_workspace_report(root)
    return {"workspace": str(root), "files": inventory, "new_blobs": len(new_blob_ids),
            "exact_duplicates": sum(item["classification"] == "exact_duplicate" for item in inventory),
            "new_likely_revision_candidates": proposed,
            "new_no_confident_match_assessments": no_match, "report": str(report)}


def _artifact_order(connection, artifact_id):
    versions = {row["id"] for row in connection.execute(
        "SELECT id FROM evidence_versions WHERE artifact_id = ?", (artifact_id,))}
    edges = [(row["before_version_id"], row["after_version_id"]) for row in connection.execute(
        """SELECT before_version_id, after_version_id FROM version_relationships
           WHERE artifact_id = ? AND status = 'active'""", (artifact_id,))]
    incoming = {version: set() for version in versions}
    outgoing = {version: set() for version in versions}
    for before, after in edges:
        if before not in versions or after not in versions:
            raise ValueError("Active relationship crosses artifact boundaries")
        incoming[after].add(before)
        outgoing[before].add(after)
    order = []
    ambiguous = False
    while incoming:
        ready = sorted(version for version, parents in incoming.items() if not parents)
        if not ready:
            raise ValueError("Confirmed version ordering contains a cycle")
        ambiguous |= len(ready) > 1
        for version in ready:
            order.append(version)
            incoming.pop(version)
            for child in outgoing[version]:
                if child in incoming:
                    incoming[child].discard(version)
    return order, ambiguous


def _record_history(connection, event_type, *, artifact_id=None, version_id=None,
                    relationship_id=None, candidate_id=None, before=None, after=None,
                    reason=None, recorded_at=None):
    history_id = "hist_" + uuid.uuid4().hex[:20]
    connection.execute(
        """INSERT INTO decision_history
           (id, event_type, artifact_id, version_id, relationship_id, candidate_id,
            before_json, after_json, reason, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (history_id, event_type, artifact_id, version_id, relationship_id, candidate_id,
         _json(before) if before is not None else None,
         _json(after) if after is not None else None, reason, recorded_at or _now()))
    return history_id


def _create_artifact(connection, name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Artifact name is required")
    artifact_id = "art_" + uuid.uuid4().hex[:20]
    timestamp = _now()
    connection.execute("INSERT INTO artifacts(id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                       (artifact_id, name.strip(), timestamp, timestamp))
    return artifact_id


def _version_for_blob(connection, artifact_id, blob_id):
    return connection.execute(
        "SELECT * FROM evidence_versions WHERE artifact_id = ? AND blob_id = ?",
        (artifact_id, blob_id)).fetchone()


def _create_version(connection, artifact_id, blob_id, *, reason, record=True):
    if not connection.execute("SELECT 1 FROM artifacts WHERE id = ?", (artifact_id,)).fetchone():
        raise ValueError("Unknown artifact ID")
    if not connection.execute("SELECT 1 FROM file_blobs WHERE id = ?", (blob_id,)).fetchone():
        raise ValueError("Unknown file blob ID")
    existing = _version_for_blob(connection, artifact_id, blob_id)
    if existing:
        return existing["id"], True
    version_id = "ev_" + uuid.uuid4().hex[:20]
    connection.execute(
        "INSERT INTO evidence_versions(id, artifact_id, blob_id, created_at) VALUES (?, ?, ?, ?)",
        (version_id, artifact_id, blob_id, _now()))
    if record:
        _record_history(connection, "version_created", artifact_id=artifact_id,
                        version_id=version_id, after={"blob_id": blob_id}, reason=reason)
    return version_id, False


def create_logical_version(workspace, blob_id, *, artifact_id=None, artifact_name=None,
                           reason="Explicit logical version creation"):
    root = _workspace_path(workspace)
    with _connect(root) as connection:
        if artifact_name:
            if artifact_id:
                raise ValueError("Specify artifact ID or a new artifact name, not both")
            artifact_id = _create_artifact(connection, artifact_name)
        if not artifact_id:
            raise ValueError("An artifact ID or new artifact name is required")
        version_id, existing = _create_version(connection, artifact_id, blob_id,
                                                reason=_require_reason(reason))
    from .workspace_report import write_workspace_report
    report = write_workspace_report(root)
    return {"artifact_id": artifact_id, "version_id": version_id, "blob_id": blob_id,
            "existing": existing, "report": str(report)}


def _comparison_inputs(root, connection, before_id, after_id, temporary):
    paths = []
    for marker, version_id in (("before", before_id), ("after", after_id)):
        row = connection.execute(
            """SELECT ev.blob_id, b.object_path, b.sha256, b.extension
               FROM evidence_versions ev JOIN file_blobs b ON b.id = ev.blob_id
               WHERE ev.id = ?""", (version_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown evidence version")
        name_row = connection.execute(
            "SELECT observed_name FROM file_occurrences WHERE blob_id = ? ORDER BY first_seen_at, id LIMIT 1",
            (row["blob_id"],)).fetchone()
        safe_name = Path(name_row["observed_name"] if name_row else marker + row["extension"]).name
        target = Path(temporary) / f"{marker}__{safe_name}"
        shutil.copyfile(root / row["object_path"], target)
        if hashlib.sha256(target.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Stored file blob failed hash verification")
        paths.append(target)
    return paths


def _ensure_comparison(root, connection, relationship_id):
    existing = connection.execute(
        "SELECT report_path FROM comparison_runs WHERE relationship_id = ?", (relationship_id,)).fetchone()
    if existing and (root / existing["report_path"]).is_file():
        return root / existing["report_path"]
    relationship = connection.execute(
        "SELECT before_version_id, after_version_id, candidate_id FROM version_relationships WHERE id = ?",
        (relationship_id,)).fetchone()
    if relationship is None:
        raise ValueError("Unknown confirmed version relationship")
    final = root / "comparisons" / relationship_id
    temporary_report = root / "comparisons" / (relationship_id + ".tmp-" + uuid.uuid4().hex)
    temporary_report.mkdir()
    structural_relative = None
    try:
        with tempfile.TemporaryDirectory(prefix="evidence-versions-") as temporary:
            inputs = _comparison_inputs(root, connection, relationship["before_version_id"],
                                        relationship["after_version_id"], temporary)
            save_workbook_analysis(inputs, temporary_report / "exact", same_layout=True)
            candidate = connection.execute(
                "SELECT evidence_json FROM candidates WHERE id = ?", (relationship["candidate_id"],)
            ).fetchone() if relationship["candidate_id"] else None
            evidence = _load_json(candidate["evidence_json"]) if candidate else {}
            if evidence.get("general_correspondence"):
                save_workbook_analysis(inputs, temporary_report / "structural", same_layout=False)
                structural_relative = (Path("comparisons") / relationship_id /
                                       "structural" / "index.html").as_posix()
        if final.exists():
            shutil.rmtree(final)
        temporary_report.replace(final)
    except Exception:
        if temporary_report.exists():
            shutil.rmtree(temporary_report)
        raise
    report_relative = (Path("comparisons") / relationship_id / "exact" / "index.html").as_posix()
    if existing:
        connection.execute(
            """UPDATE comparison_runs SET report_path = ?, structural_report_path = ?,
               created_at = ? WHERE relationship_id = ?""",
            (report_relative, structural_relative, _now(), relationship_id))
    else:
        connection.execute(
            """INSERT INTO comparison_runs
               (id, relationship_id, report_path, structural_report_path, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            ("cmp_" + uuid.uuid4().hex[:20], relationship_id, report_relative,
             structural_relative, _now()))
    return root / report_relative


def _artifact_for_confirmation(connection, blob_pair, artifact_id, artifact_name):
    if artifact_id and artifact_name:
        raise ValueError("Specify artifact ID or a new artifact name, not both")
    if artifact_name:
        return _create_artifact(connection, artifact_name)
    if artifact_id:
        if not connection.execute("SELECT 1 FROM artifacts WHERE id = ?", (artifact_id,)).fetchone():
            raise ValueError("Unknown artifact ID")
        return artifact_id
    assigned = {row["artifact_id"] for blob in blob_pair for row in connection.execute(
        "SELECT artifact_id FROM evidence_versions WHERE blob_id = ?", (blob,))}
    if len(assigned) == 1:
        return next(iter(assigned))
    if len(assigned) > 1:
        raise ValueError("Candidate blobs have versions in multiple artifacts; specify --artifact-id")
    raise ValueError("A new version family requires --artifact-name")


def confirm_candidate(workspace, candidate_id, before_blob_id, artifact_name=None,
                      artifact_id=None, override_no_match=False):
    root = _workspace_path(workspace)
    with _connect(root) as connection:
        candidate = connection.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if candidate is None:
            raise ValueError("Unknown version candidate")
        if candidate["status"] == "rejected":
            raise ValueError("Candidate was rejected; that decision is preserved")
        if candidate["classification"] != "likely_revision" and not override_no_match:
            raise ValueError("This pair had no confident match; use --override-no-match for an explicit manual link")
        pair = {candidate["left_blob_id"], candidate["right_blob_id"]}
        if before_blob_id not in pair:
            raise ValueError("--before must be one of the candidate's file blob IDs")
        after_blob_id = next(iter(pair - {before_blob_id}))
        chosen_artifact = _artifact_for_confirmation(connection, pair, artifact_id, artifact_name)
        before_version, _ = _create_version(connection, chosen_artifact, before_blob_id,
                                            reason="Created by candidate confirmation")
        after_version, _ = _create_version(connection, chosen_artifact, after_blob_id,
                                           reason="Created by candidate confirmation")
        active = connection.execute(
            """SELECT id FROM version_relationships
               WHERE artifact_id = ? AND before_version_id = ? AND after_version_id = ?
                 AND status = 'active'""",
            (chosen_artifact, before_version, after_version)).fetchone()
        if active:
            report = _ensure_comparison(root, connection, active["id"])
            relationship_id = active["id"]
            existing = True
        else:
            relationship_id = "rel_" + uuid.uuid4().hex[:20]
            timestamp = _now()
            connection.execute(
                """INSERT INTO version_relationships
                   (id, artifact_id, before_version_id, after_version_id, candidate_id,
                    status, confirmed_at, updated_at) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)""",
                (relationship_id, chosen_artifact, before_version, after_version,
                 candidate_id, timestamp, timestamp))
            _artifact_order(connection, chosen_artifact)
            connection.execute("UPDATE candidates SET status = 'confirmed', decided_at = ? WHERE id = ?",
                               (timestamp, candidate_id))
            _record_history(
                connection, "candidate_confirmed", artifact_id=chosen_artifact,
                relationship_id=relationship_id, candidate_id=candidate_id,
                after={"before_blob_id": before_blob_id, "after_blob_id": after_blob_id,
                       "before_version_id": before_version, "after_version_id": after_version},
                reason="User confirmed version family and ordering", recorded_at=timestamp)
            report = _ensure_comparison(root, connection, relationship_id)
            existing = False
    from .workspace_report import write_workspace_report
    workspace_report = write_workspace_report(root)
    return {"candidate_id": candidate_id, "confirmed": True, "existing": existing,
            "artifact_id": chosen_artifact, "relationship_id": relationship_id,
            "before_blob_id": before_blob_id, "after_blob_id": after_blob_id,
            "before_version_id": before_version, "after_version_id": after_version,
            "comparison_report": str(report), "workspace_report": str(workspace_report)}


def reject_candidate(workspace, candidate_id):
    root = _workspace_path(workspace)
    with _connect(root) as connection:
        candidate = connection.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if candidate is None:
            raise ValueError("Unknown version candidate")
        if candidate["status"] == "confirmed":
            raise ValueError("Withdraw confirmed relationships before rejecting their candidate")
        if candidate["status"] != "rejected":
            timestamp = _now()
            connection.execute("UPDATE candidates SET status = 'rejected', decided_at = ? WHERE id = ?",
                               (timestamp, candidate_id))
            _record_history(connection, "candidate_rejected", candidate_id=candidate_id,
                            after={"status": "rejected"}, reason="User rejected candidate",
                            recorded_at=timestamp)
    from .workspace_report import write_workspace_report
    report = write_workspace_report(root)
    return {"candidate_id": candidate_id, "rejected": True, "report": str(report)}


def _withdraw_relationship(connection, relationship, reason, event_type="relationship_withdrawn"):
    if relationship["status"] != "active":
        raise ValueError("Only an active relationship can be withdrawn")
    timestamp = _now()
    before = {key: relationship[key] for key in
              ("artifact_id", "before_version_id", "after_version_id", "status")}
    connection.execute(
        """UPDATE version_relationships SET status = 'withdrawn', withdrawn_at = ?,
           updated_at = ? WHERE id = ?""", (timestamp, timestamp, relationship["id"]))
    if relationship["candidate_id"]:
        remaining = connection.execute(
            "SELECT 1 FROM version_relationships WHERE candidate_id = ? AND status = 'active'",
            (relationship["candidate_id"],)).fetchone()
        if not remaining:
            connection.execute("UPDATE candidates SET status = 'withdrawn', decided_at = ? WHERE id = ?",
                               (timestamp, relationship["candidate_id"]))
    _record_history(connection, event_type, artifact_id=relationship["artifact_id"],
                    relationship_id=relationship["id"], candidate_id=relationship["candidate_id"],
                    before=before, after={**before, "status": "withdrawn"}, reason=reason,
                    recorded_at=timestamp)


def withdraw_relationship(workspace, relationship_id, reason):
    root = _workspace_path(workspace)
    reason = _require_reason(reason)
    with _connect(root) as connection:
        relationship = connection.execute(
            "SELECT * FROM version_relationships WHERE id = ?", (relationship_id,)).fetchone()
        if relationship is None:
            raise ValueError("Unknown version relationship")
        _withdraw_relationship(connection, relationship, reason)
    from .workspace_report import write_workspace_report
    report = write_workspace_report(root)
    return {"relationship_id": relationship_id, "status": "withdrawn", "report": str(report)}


def reassign_version(workspace, version_id, *, artifact_id=None, artifact_name=None, reason):
    root = _workspace_path(workspace)
    reason = _require_reason(reason)
    with _connect(root) as connection:
        version = connection.execute("SELECT * FROM evidence_versions WHERE id = ?", (version_id,)).fetchone()
        if version is None:
            raise ValueError("Unknown evidence version")
        if artifact_id and artifact_name:
            raise ValueError("Specify artifact ID or a new artifact name, not both")
        target = _create_artifact(connection, artifact_name) if artifact_name else artifact_id
        if not target or not connection.execute("SELECT 1 FROM artifacts WHERE id = ?", (target,)).fetchone():
            raise ValueError("A valid target artifact is required")
        if target == version["artifact_id"]:
            raise ValueError("Evidence version already belongs to that artifact")
        if _version_for_blob(connection, target, version["blob_id"]):
            raise ValueError("Target artifact already has a logical version backed by this file blob")
        relationships = connection.execute(
            """SELECT * FROM version_relationships WHERE status = 'active'
               AND (before_version_id = ? OR after_version_id = ?)""", (version_id, version_id)).fetchall()
        for relationship in relationships:
            _withdraw_relationship(connection, relationship,
                                   "Withdrawn because version was reassigned: " + reason)
        old_artifact = version["artifact_id"]
        connection.execute("UPDATE evidence_versions SET artifact_id = ? WHERE id = ?", (target, version_id))
        _record_history(connection, "version_reassigned", artifact_id=target, version_id=version_id,
                        before={"artifact_id": old_artifact, "blob_id": version["blob_id"]},
                        after={"artifact_id": target, "blob_id": version["blob_id"]}, reason=reason)
        _artifact_order(connection, old_artifact)
        _artifact_order(connection, target)
    from .workspace_report import write_workspace_report
    report = write_workspace_report(root)
    return {"version_id": version_id, "from_artifact_id": old_artifact,
            "to_artifact_id": target, "withdrawn_relationships": [row["id"] for row in relationships],
            "report": str(report)}


def correct_order(workspace, relationship_id, before_version_id, reason):
    root = _workspace_path(workspace)
    reason = _require_reason(reason)
    with _connect(root) as connection:
        old = connection.execute("SELECT * FROM version_relationships WHERE id = ?", (relationship_id,)).fetchone()
        if old is None or old["status"] != "active":
            raise ValueError("Ordering can be corrected only on an active relationship")
        pair = {old["before_version_id"], old["after_version_id"]}
        if before_version_id not in pair:
            raise ValueError("--before must be one of the relationship's version IDs")
        if before_version_id == old["before_version_id"]:
            raise ValueError("Requested ordering is already active")
        after_version_id = next(iter(pair - {before_version_id}))
        timestamp = _now()
        connection.execute(
            "UPDATE version_relationships SET status = 'superseded', withdrawn_at = ?, updated_at = ? WHERE id = ?",
            (timestamp, timestamp, relationship_id))
        new_id = "rel_" + uuid.uuid4().hex[:20]
        connection.execute(
            """INSERT INTO version_relationships
               (id, artifact_id, before_version_id, after_version_id, candidate_id,
                status, confirmed_at, updated_at, supersedes_relationship_id)
               VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?)""",
            (new_id, old["artifact_id"], before_version_id, after_version_id,
             old["candidate_id"], timestamp, timestamp, relationship_id))
        _artifact_order(connection, old["artifact_id"])
        _record_history(connection, "order_corrected", artifact_id=old["artifact_id"], relationship_id=new_id,
                        candidate_id=old["candidate_id"],
                        before={"relationship_id": relationship_id,
                                "before_version_id": old["before_version_id"],
                                "after_version_id": old["after_version_id"]},
                        after={"relationship_id": new_id, "before_version_id": before_version_id,
                               "after_version_id": after_version_id}, reason=reason, recorded_at=timestamp)
        report = _ensure_comparison(root, connection, new_id)
    from .workspace_report import write_workspace_report
    workspace_report = write_workspace_report(root)
    return {"superseded_relationship_id": relationship_id, "relationship_id": new_id,
            "before_version_id": before_version_id, "after_version_id": after_version_id,
            "comparison_report": str(report), "workspace_report": str(workspace_report)}


def rename_artifact(workspace, artifact_id, name, reason):
    root = _workspace_path(workspace)
    reason = _require_reason(reason)
    if not isinstance(name, str) or not name.strip():
        raise ValueError("New artifact name is required")
    with _connect(root) as connection:
        artifact = connection.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
        if artifact is None:
            raise ValueError("Unknown artifact ID")
        timestamp = _now()
        connection.execute("UPDATE artifacts SET name = ?, updated_at = ? WHERE id = ?",
                           (name.strip(), timestamp, artifact_id))
        _record_history(connection, "artifact_renamed", artifact_id=artifact_id,
                        before={"name": artifact["name"]}, after={"name": name.strip()},
                        reason=reason, recorded_at=timestamp)
    from .workspace_report import write_workspace_report
    report = write_workspace_report(root)
    return {"artifact_id": artifact_id, "old_name": artifact["name"],
            "new_name": name.strip(), "report": str(report)}


def workspace_state(workspace):
    root = _workspace_path(workspace)
    with _connect(root) as connection:
        workspace_row = dict(connection.execute("SELECT * FROM workspace").fetchone())
        blobs = []
        for row in connection.execute("SELECT * FROM file_blobs ORDER BY first_seen_at, id"):
            item = dict(row)
            item["fingerprint"] = _load_json(item.pop("fingerprint_json"))
            item["occurrences"] = [dict(value) for value in connection.execute(
                """SELECT source_path, observed_name, first_seen_at, last_seen_at
                   FROM file_occurrences WHERE blob_id = ? ORDER BY first_seen_at, id""", (row["id"],))]
            item["display_name"] = (item["occurrences"][0]["observed_name"]
                                    if item["occurrences"] else item["sha256"][:16])
            item["version_ids"] = [value["id"] for value in connection.execute(
                "SELECT id FROM evidence_versions WHERE blob_id = ? ORDER BY created_at, id", (row["id"],))]
            blobs.append(item)
        versions = [dict(row) for row in connection.execute(
            "SELECT * FROM evidence_versions ORDER BY created_at, id")]
        candidates = []
        for row in connection.execute("SELECT * FROM candidates ORDER BY created_at, id"):
            item = dict(row)
            item["evidence"] = _load_json(item.pop("evidence_json"))
            candidates.append(item)
        artifacts = []
        for row in connection.execute("SELECT * FROM artifacts ORDER BY created_at, id"):
            item = dict(row)
            order, ambiguous = _artifact_order(connection, row["id"])
            item["version_order"] = order
            item["ordering_ambiguous"] = ambiguous
            item["relationships"] = [dict(value) for value in connection.execute(
                "SELECT * FROM version_relationships WHERE artifact_id = ? ORDER BY confirmed_at, id", (row["id"],))]
            artifacts.append(item)
        comparisons = [dict(row) for row in connection.execute(
            "SELECT * FROM comparison_runs ORDER BY created_at, id")]
        history = [dict(row) for row in connection.execute(
            "SELECT * FROM decision_history ORDER BY recorded_at, id")]
        for event in history:
            event["before"] = _load_json(event.pop("before_json")) if event["before_json"] else None
            event["after"] = _load_json(event.pop("after_json")) if event["after_json"] else None
    return {"schema_version": SCHEMA_VERSION, "workspace_path": str(root),
            "workspace": workspace_row, "file_blobs": blobs, "evidence_versions": versions,
            "candidates": candidates, "artifacts": artifacts, "comparisons": comparisons,
            "decision_history": history}
