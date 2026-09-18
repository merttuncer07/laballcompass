"""Persistent, local evidence-version workspaces.

This module deliberately models workbook identity and version relationships only.
Cell/formula dependencies remain in the existing workbench contracts and are
invoked only when confirmed versions are compared.
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
from .cli import save_workbook_analysis
from .workbooks import open_workbooks


SCHEMA_VERSION = 1
DATABASE_NAME = "workspace.sqlite3"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _load_json(value):
    return json.loads(value) if value else {}


def _workspace_path(path):
    return Path(path).expanduser().resolve()


@contextmanager
def _connect(path):
    root = _workspace_path(path)
    database = root / DATABASE_NAME
    if not database.is_file():
        raise ValueError(f"Not an evidence workspace: {root}")
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version != SCHEMA_VERSION:
        connection.close()
        raise ValueError(f"Unsupported evidence workspace schema: {version}")
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
        return {"workspace": str(root), "id": row["id"], "name": row["name"], "created": False}
    if any(root.iterdir()):
        raise ValueError("A new workspace folder must be empty")
    (root / "objects").mkdir()
    (root / "comparisons").mkdir()
    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE workspace (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE evidence_versions (
                id TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL UNIQUE,
                extension TEXT NOT NULL,
                object_path TEXT NOT NULL UNIQUE,
                size_bytes INTEGER NOT NULL,
                first_name TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                fingerprint_json TEXT NOT NULL
            );
            CREATE TABLE occurrences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_id TEXT NOT NULL REFERENCES evidence_versions(id),
                source_path TEXT NOT NULL,
                observed_name TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                UNIQUE(version_id, source_path)
            );
            CREATE TABLE artifacts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE artifact_versions (
                artifact_id TEXT NOT NULL REFERENCES artifacts(id),
                version_id TEXT NOT NULL UNIQUE REFERENCES evidence_versions(id),
                added_at TEXT NOT NULL,
                PRIMARY KEY(artifact_id, version_id)
            );
            CREATE TABLE candidates (
                id TEXT PRIMARY KEY,
                left_version_id TEXT NOT NULL REFERENCES evidence_versions(id),
                right_version_id TEXT NOT NULL REFERENCES evidence_versions(id),
                classification TEXT NOT NULL,
                status TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                decided_at TEXT,
                UNIQUE(left_version_id, right_version_id)
            );
            CREATE TABLE version_relationships (
                id TEXT PRIMARY KEY,
                artifact_id TEXT NOT NULL REFERENCES artifacts(id),
                before_version_id TEXT NOT NULL REFERENCES evidence_versions(id),
                after_version_id TEXT NOT NULL REFERENCES evidence_versions(id),
                candidate_id TEXT REFERENCES candidates(id),
                confirmed_at TEXT NOT NULL,
                UNIQUE(artifact_id, before_version_id, after_version_id),
                CHECK(before_version_id <> after_version_id)
            );
            CREATE TABLE confirmations (
                id TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL REFERENCES candidates(id),
                decision TEXT NOT NULL,
                artifact_id TEXT REFERENCES artifacts(id),
                before_version_id TEXT REFERENCES evidence_versions(id),
                after_version_id TEXT REFERENCES evidence_versions(id),
                recorded_at TEXT NOT NULL
            );
            CREATE TABLE comparison_runs (
                id TEXT PRIMARY KEY,
                relationship_id TEXT NOT NULL UNIQUE REFERENCES version_relationships(id),
                report_path TEXT NOT NULL,
                structural_report_path TEXT,
                created_at TEXT NOT NULL
            );
            PRAGMA user_version = 1;
            """
        )
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
    return {"workspace": str(root), "id": wid, "name": name or root.name, "created": True}


def _fingerprint(path, workbook):
    sheets = []
    formula_hashes = set()
    total_populated = 0
    total_formulas = 0
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
        sheets.append({
            "name": sheet.title,
            "max_row": sheet.max_row,
            "max_column": sheet.max_column,
            "populated_cells": populated,
            "formula_cells": formulas,
        })
    return {
        "schema_version": 1,
        "analyzed_name": Path(path).name,
        "sheet_names": [sheet["name"] for sheet in sheets],
        "sheets": sheets,
        "sheet_count": len(sheets),
        "populated_cells": total_populated,
        "formula_cells": total_formulas,
        "formula_hashes": sorted(formula_hashes),
    }


def _version_id(sha256):
    return "ev_" + sha256[:20]


def _candidate_id(left_id, right_id):
    left_id, right_id = sorted((left_id, right_id))
    return "cand_" + hashlib.sha256((left_id + "\0" + right_id).encode()).hexdigest()[:20]


def _ratio(a, b):
    return min(a, b) / max(a, b) if max(a, b) else 1.0


def _candidate_evidence(left, right, paths, books):
    left_sheets = set(left["sheet_names"])
    right_sheets = set(right["sheet_names"])
    union = left_sheets | right_sheets
    sheet_overlap = len(left_sheets & right_sheets) / len(union) if union else 1.0
    populated_ratio = _ratio(left["populated_cells"], right["populated_cells"])
    formula_left = set(left["formula_hashes"])
    formula_right = set(right["formula_hashes"])
    formula_common = len(formula_left & formula_right)
    formula_overlap = formula_common / min(len(formula_left), len(formula_right)) if min(len(formula_left), len(formula_right)) else 0.0
    filename_similarity = SequenceMatcher(
        None, Path(left["analyzed_name"]).stem.casefold(), Path(right["analyzed_name"]).stem.casefold()
    ).ratio()
    evidence = {
        "schema_version": 1,
        "structure": {
            "left_sheet_count": left["sheet_count"],
            "right_sheet_count": right["sheet_count"],
            "common_sheet_names": sorted(left_sheets & right_sheets),
            "sheet_name_overlap": round(sheet_overlap, 6),
            "populated_cell_count_ratio": round(populated_ratio, 6),
            "common_formula_text_hashes": formula_common,
            "formula_text_overlap_of_smaller_set": round(formula_overlap, 6),
        },
        "filename_similarity": round(filename_similarity, 6),
        "filename_role": "Explanatory only; filename similarity never establishes a version relationship.",
        "reasons": [],
        "cautions": [
            "Likely revision is a proposal, not confirmed provenance.",
            "Similar content does not prove common origin.",
        ],
    }
    plausible_gate = (
        (sheet_overlap >= 0.5 and populated_ratio >= 0.4)
        or (formula_common >= 3 and formula_overlap >= 0.4)
        or (left["sheet_count"] == right["sheet_count"] and populated_ratio >= 0.8)
    )
    if not plausible_gate:
        evidence["reasons"].append("Insufficient structural overlap to run the bounded content matcher.")
        return "no_confident_match", evidence

    same_layout = left_sheets == right_sheets and bool(left_sheets)
    try:
        exact = compare_content(paths, books, same_layout=same_layout)
    except ValueError as error:
        evidence["reasons"].append("Candidate content assessment stopped at a safety limit: " + str(error))
        evidence["assessment_incomplete"] = True
        return "no_confident_match", evidence
    if same_layout:
        compared = sum(block["compared_positions"] for block in exact["blocks"])
        matching_values = sum(block["matching_cells"] for block in exact["blocks"])
        matching_formulas = sum(block["matching_formula_cells"] for block in exact["blocks"])
        changed = sum(block["changed_cells"] for block in exact["blocks"])
        uncomparable = sum(block["uncompared_cells"] for block in exact["blocks"])
        matching = matching_values + matching_formulas
        fraction = matching / compared if compared else 0.0
        evidence["same_layout"] = {
            "compared_positions": compared,
            "matching_literal_values": matching_values,
            "matching_formula_texts": matching_formulas,
            "changed_or_added_removed_positions": changed,
            "uncomparable_positions": uncomparable,
            "unchanged_fraction": round(fraction, 6),
        }
        small_strong = compared >= 6 and matching >= 6 and fraction >= 0.8
        large_supported = compared >= 20 and matching >= max(12, int(compared * 0.55))
        formula_supported = formula_common >= 3 and formula_overlap >= 0.6 and populated_ratio >= 0.5
        exact_supported = small_strong or large_supported or formula_supported
        if exact_supported:
            evidence["reasons"].append(
                f"Same named-sheet coordinates contain {matching} unchanged values/formulas across {compared} positions."
            )
            if fraction >= 0.8:
                return "likely_revision", evidence
        # A same-sheet pair with many coordinate changes may be a reordered revision.
        # Reuse the existing general matcher before rejecting it.
        if compared and fraction < 0.8:
            try:
                exact = compare_content(paths, books, same_layout=False)
            except ValueError as error:
                evidence["reasons"].append("General correspondence assessment stopped at a safety limit: " + str(error))
                evidence["assessment_incomplete"] = True
                return ("likely_revision" if exact_supported else "no_confident_match"), evidence

    blocks = exact["blocks"]
    best = max(blocks, key=lambda block: (block.get("matching_cells", 0), block.get("match_fraction") or 0), default=None)
    if best is not None:
        best_matching = best.get("matching_cells", 0)
        best_fraction = best.get("match_fraction") or 0.0
        minimum = max(12, min(100, int(min(left["populated_cells"], right["populated_cells"]) * 0.05)))
        evidence["general_correspondence"] = {
            "kind": best.get("kind"),
            "matching_cells": best_matching,
            "compared_positions": best.get("compared_positions", 0),
            "match_fraction": round(best_fraction, 6),
            "minimum_matching_cells_required": minimum,
            "left": best.get("left"),
            "right": best.get("right"),
            "total_candidate_regions": exact.get("total_blocks_found", len(blocks)),
            "ambiguous_rows_omitted": exact.get("record_alignment", {}).get("ambiguous_rows_omitted", 0),
        }
        independent_structure = populated_ratio >= 0.5 and (
            sheet_overlap >= 0.5 or formula_common >= 3 or left["sheet_count"] == right["sheet_count"]
        )
        if independent_structure and best_matching >= minimum and best_fraction >= 0.9:
            evidence["reasons"].append(
                f"The existing {best.get('kind')} matcher found {best_matching} matching cells at {best_fraction:.1%} agreement."
            )
            return "likely_revision", evidence
    if same_layout and evidence.get("same_layout"):
        summary = evidence["same_layout"]
        compared = summary["compared_positions"]
        matching = summary["matching_literal_values"] + summary["matching_formula_texts"]
        if ((compared >= 6 and matching >= 6 and summary["unchanged_fraction"] >= 0.8)
                or (compared >= 20 and matching >= max(12, int(compared * 0.55)))
                or (formula_common >= 3 and formula_overlap >= 0.6 and populated_ratio >= 0.5)):
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


def import_folder(workspace, folder):
    root = _workspace_path(workspace)
    source_root = Path(folder).expanduser().resolve()
    if not source_root.is_dir():
        raise ValueError("Import source must be a folder")
    paths = sorted(
        (path for path in source_root.iterdir()
         if path.is_file() and path.suffix.lower() in (".xlsx", ".xlsm") and not path.name.startswith("~$")),
        key=lambda path: path.name.casefold(),
    )
    if not paths:
        raise ValueError("Folder contains no .xlsx or .xlsm files")
    if len(paths) > 20:
        raise ValueError("Supply at most 20 workbooks per import")
    before_hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    inventory = []
    new_ids = []
    with open_workbooks(paths) as (loaded_paths, books):
        fingerprints = [_fingerprint(path, book) for path, book in zip(loaded_paths, books)]
        with _connect(root) as connection:
            for path, book, fingerprint in zip(loaded_paths, books, fingerprints):
                sha256 = book._lab_input_sha256
                existing = connection.execute(
                    "SELECT id, object_path FROM evidence_versions WHERE sha256 = ?", (sha256,)
                ).fetchone()
                timestamp = _now()
                if existing:
                    version_id = existing["id"]
                    stored = root / existing["object_path"]
                    if not stored.is_file() or hashlib.sha256(stored.read_bytes()).hexdigest() != sha256:
                        raise ValueError("Stored evidence object is missing or failed hash verification")
                    classification = "exact_duplicate"
                    connection.execute(
                        "UPDATE evidence_versions SET last_seen_at = ? WHERE id = ?", (timestamp, version_id)
                    )
                else:
                    version_id = _version_id(sha256)
                    object_path = _store_object(root, path, sha256, path.suffix)
                    connection.execute(
                        """INSERT INTO evidence_versions
                           (id, sha256, extension, object_path, size_bytes, first_name,
                            first_seen_at, last_seen_at, fingerprint_json)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (version_id, sha256, path.suffix.lower(), object_path, path.stat().st_size,
                         path.name, timestamp, timestamp, _json(fingerprint)),
                    )
                    new_ids.append(version_id)
                    classification = "new_version"
                occurrence = connection.execute(
                    "SELECT id FROM occurrences WHERE version_id = ? AND source_path = ?",
                    (version_id, str(path)),
                ).fetchone()
                if occurrence:
                    connection.execute(
                        "UPDATE occurrences SET last_seen_at = ? WHERE id = ?", (timestamp, occurrence["id"])
                    )
                else:
                    connection.execute(
                        """INSERT INTO occurrences
                           (version_id, source_path, observed_name, first_seen_at, last_seen_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (version_id, str(path), path.name, timestamp, timestamp),
                    )
                inventory.append({
                    "path": str(path), "name": path.name, "version_id": version_id,
                    "sha256": sha256, "classification": classification,
                })

    proposed = 0
    no_match = 0
    with _connect(root) as connection:
        rows = connection.execute(
            "SELECT id, object_path, fingerprint_json FROM evidence_versions ORDER BY first_seen_at, id"
        ).fetchall()
        by_id = {row["id"]: row for row in rows}
        pairs = set()
        for new_id in new_ids:
            for other_id in by_id:
                if new_id == other_id:
                    continue
                pairs.add(tuple(sorted((new_id, other_id))))
        for left_id, right_id in sorted(pairs):
            if connection.execute(
                "SELECT 1 FROM candidates WHERE left_version_id = ? AND right_version_id = ?",
                (left_id, right_id),
            ).fetchone():
                continue
            left_row, right_row = by_id[left_id], by_id[right_id]
            candidate_paths = [root / left_row["object_path"], root / right_row["object_path"]]
            with open_workbooks(candidate_paths, preserve_order=True) as (opened_paths, books):
                classification, evidence = _candidate_evidence(
                    _load_json(left_row["fingerprint_json"]),
                    _load_json(right_row["fingerprint_json"]),
                    opened_paths,
                    books,
                )
            status = "pending" if classification == "likely_revision" else "observed"
            connection.execute(
                """INSERT INTO candidates
                   (id, left_version_id, right_version_id, classification, status,
                    evidence_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (_candidate_id(left_id, right_id), left_id, right_id, classification,
                 status, _json(evidence), _now()),
            )
            proposed += int(classification == "likely_revision")
            no_match += int(classification == "no_confident_match")
    after_hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    if before_hashes != after_hashes:
        raise RuntimeError("An original evidence file changed during import")
    from .workspace_report import write_workspace_report
    report = write_workspace_report(root)
    return {
        "workspace": str(root),
        "files": inventory,
        "new_versions": len(new_ids),
        "exact_duplicates": sum(item["classification"] == "exact_duplicate" for item in inventory),
        "new_likely_revision_candidates": proposed,
        "new_no_confident_match_assessments": no_match,
        "report": str(report),
    }


def _artifact_order(connection, artifact_id):
    versions = {row["version_id"] for row in connection.execute(
        "SELECT version_id FROM artifact_versions WHERE artifact_id = ?", (artifact_id,)
    )}
    edges = [(row["before_version_id"], row["after_version_id"]) for row in connection.execute(
        "SELECT before_version_id, after_version_id FROM version_relationships WHERE artifact_id = ?",
        (artifact_id,),
    )]
    incoming = {version: set() for version in versions}
    outgoing = {version: set() for version in versions}
    for before, after in edges:
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


def _comparison_inputs(root, connection, before_id, after_id, temporary):
    rows = []
    for marker, version_id in (("before", before_id), ("after", after_id)):
        row = connection.execute(
            "SELECT first_name, object_path, sha256 FROM evidence_versions WHERE id = ?", (version_id,)
        ).fetchone()
        if row is None:
            raise ValueError("Unknown evidence version")
        safe_name = Path(row["first_name"]).name
        target = Path(temporary) / f"{marker}__{safe_name}"
        shutil.copyfile(root / row["object_path"], target)
        if hashlib.sha256(target.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Stored evidence object failed hash verification")
        rows.append(target)
    return rows


def _ensure_comparison(root, connection, relationship_id):
    existing = connection.execute(
        "SELECT report_path FROM comparison_runs WHERE relationship_id = ?", (relationship_id,)
    ).fetchone()
    if existing and (root / existing["report_path"]).is_file():
        return root / existing["report_path"]
    relationship = connection.execute(
        """SELECT before_version_id, after_version_id, candidate_id
           FROM version_relationships WHERE id = ?""", (relationship_id,)
    ).fetchone()
    if relationship is None:
        raise ValueError("Unknown confirmed version relationship")
    final = root / "comparisons" / relationship_id
    if final.exists():
        shutil.rmtree(final)
    temporary_report = root / "comparisons" / (relationship_id + ".tmp-" + uuid.uuid4().hex)
    temporary_report.mkdir()
    structural_relative = None
    with tempfile.TemporaryDirectory(prefix="evidence-versions-") as temporary:
        inputs = _comparison_inputs(
            root, connection, relationship["before_version_id"], relationship["after_version_id"], temporary
        )
        exact_folder = temporary_report / "exact"
        report = save_workbook_analysis(inputs, exact_folder, same_layout=True)
        candidate = connection.execute(
            "SELECT evidence_json FROM candidates WHERE id = ?", (relationship["candidate_id"],)
        ).fetchone() if relationship["candidate_id"] else None
        evidence = _load_json(candidate["evidence_json"]) if candidate else {}
        if evidence.get("general_correspondence"):
            structural_folder = temporary_report / "structural"
            save_workbook_analysis(inputs, structural_folder, same_layout=False)
            structural_relative = (Path("comparisons") / relationship_id / "structural" / "index.html").as_posix()
    temporary_report.replace(final)
    report_relative = (Path("comparisons") / relationship_id / "exact" / "index.html").as_posix()
    if existing:
        connection.execute(
            "UPDATE comparison_runs SET report_path = ?, structural_report_path = ?, created_at = ? WHERE relationship_id = ?",
            (report_relative, structural_relative, _now(), relationship_id),
        )
    else:
        connection.execute(
            """INSERT INTO comparison_runs
               (id, relationship_id, report_path, structural_report_path, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            ("cmp_" + uuid.uuid4().hex[:20], relationship_id, report_relative, structural_relative, _now()),
        )
    return root / report_relative


def confirm_candidate(workspace, candidate_id, before_version_id, artifact_name=None,
                      artifact_id=None, override_no_match=False):
    root = _workspace_path(workspace)
    with _connect(root) as connection:
        candidate = connection.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if candidate is None:
            raise ValueError("Unknown version candidate")
        if candidate["status"] == "confirmed":
            relationship = connection.execute(
                "SELECT id FROM version_relationships WHERE candidate_id = ?", (candidate_id,)
            ).fetchone()
            report = _ensure_comparison(root, connection, relationship["id"])
            connection.commit()
            from .workspace_report import write_workspace_report
            write_workspace_report(root)
            return {"candidate_id": candidate_id, "confirmed": True, "existing": True,
                    "comparison_report": str(report)}
        if candidate["status"] == "rejected":
            raise ValueError("Candidate was rejected; decisions are preserved")
        if candidate["classification"] != "likely_revision" and not override_no_match:
            raise ValueError("This pair had no confident match; pass --override-no-match for an explicit manual link")
        pair = {candidate["left_version_id"], candidate["right_version_id"]}
        if before_version_id not in pair:
            raise ValueError("--before must be one of the candidate's version IDs")
        after_version_id = next(iter(pair - {before_version_id}))
        memberships = {}
        for version_id in pair:
            row = connection.execute(
                "SELECT artifact_id FROM artifact_versions WHERE version_id = ?", (version_id,)
            ).fetchone()
            memberships[version_id] = row["artifact_id"] if row else None
        assigned = {value for value in memberships.values() if value}
        if len(assigned) > 1:
            raise ValueError("Versions already belong to different artifacts")
        if artifact_id:
            if not connection.execute("SELECT 1 FROM artifacts WHERE id = ?", (artifact_id,)).fetchone():
                raise ValueError("Unknown artifact ID")
            if assigned and artifact_id not in assigned:
                raise ValueError("Specified artifact conflicts with existing membership")
            chosen_artifact = artifact_id
        elif assigned:
            chosen_artifact = next(iter(assigned))
        else:
            if not artifact_name:
                raise ValueError("A new version family requires --artifact-name")
            chosen_artifact = "art_" + uuid.uuid4().hex[:20]
            connection.execute(
                "INSERT INTO artifacts(id, name, created_at) VALUES (?, ?, ?)",
                (chosen_artifact, artifact_name, _now()),
            )
        for version_id in pair:
            connection.execute(
                "INSERT OR IGNORE INTO artifact_versions(artifact_id, version_id, added_at) VALUES (?, ?, ?)",
                (chosen_artifact, version_id, _now()),
            )
        relationship_id = "rel_" + uuid.uuid4().hex[:20]
        connection.execute(
            """INSERT INTO version_relationships
               (id, artifact_id, before_version_id, after_version_id, candidate_id, confirmed_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (relationship_id, chosen_artifact, before_version_id, after_version_id, candidate_id, _now()),
        )
        _artifact_order(connection, chosen_artifact)
        connection.execute(
            "UPDATE candidates SET status = 'confirmed', decided_at = ? WHERE id = ?", (_now(), candidate_id)
        )
        connection.execute(
            """INSERT INTO confirmations
               (id, candidate_id, decision, artifact_id, before_version_id, after_version_id, recorded_at)
               VALUES (?, ?, 'confirmed', ?, ?, ?, ?)""",
            ("conf_" + uuid.uuid4().hex[:20], candidate_id, chosen_artifact,
             before_version_id, after_version_id, _now()),
        )
        report = _ensure_comparison(root, connection, relationship_id)
    from .workspace_report import write_workspace_report
    workspace_report = write_workspace_report(root)
    return {
        "candidate_id": candidate_id, "confirmed": True, "existing": False,
        "artifact_id": chosen_artifact, "before": before_version_id, "after": after_version_id,
        "comparison_report": str(report), "workspace_report": str(workspace_report),
    }


def reject_candidate(workspace, candidate_id):
    root = _workspace_path(workspace)
    with _connect(root) as connection:
        candidate = connection.execute("SELECT status FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if candidate is None:
            raise ValueError("Unknown version candidate")
        if candidate["status"] == "confirmed":
            raise ValueError("A confirmed relationship cannot be rejected")
        if candidate["status"] != "rejected":
            connection.execute(
                "UPDATE candidates SET status = 'rejected', decided_at = ? WHERE id = ?", (_now(), candidate_id)
            )
            connection.execute(
                "INSERT INTO confirmations(id, candidate_id, decision, recorded_at) VALUES (?, ?, 'rejected', ?)",
                ("conf_" + uuid.uuid4().hex[:20], candidate_id, _now()),
            )
    from .workspace_report import write_workspace_report
    report = write_workspace_report(root)
    return {"candidate_id": candidate_id, "rejected": True, "report": str(report)}


def workspace_state(workspace):
    root = _workspace_path(workspace)
    with _connect(root) as connection:
        workspace_row = dict(connection.execute("SELECT * FROM workspace").fetchone())
        versions = []
        for row in connection.execute("SELECT * FROM evidence_versions ORDER BY first_seen_at, id"):
            item = dict(row)
            item["fingerprint"] = _load_json(item.pop("fingerprint_json"))
            item["occurrences"] = [dict(value) for value in connection.execute(
                "SELECT source_path, observed_name, first_seen_at, last_seen_at FROM occurrences WHERE version_id = ? ORDER BY source_path",
                (row["id"],),
            )]
            versions.append(item)
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
                "SELECT * FROM version_relationships WHERE artifact_id = ? ORDER BY confirmed_at, id", (row["id"],)
            )]
            artifacts.append(item)
        comparisons = [dict(row) for row in connection.execute(
            "SELECT * FROM comparison_runs ORDER BY created_at, id"
        )]
    return {
        "schema_version": SCHEMA_VERSION,
        "workspace_path": str(root),
        "workspace": workspace_row,
        "versions": versions,
        "candidates": candidates,
        "artifacts": artifacts,
        "comparisons": comparisons,
    }
