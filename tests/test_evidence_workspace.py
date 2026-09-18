import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from openpyxl import Workbook

from workbench.evidence_workspace import (
    confirm_candidate,
    correct_order,
    create_logical_version,
    create_workspace,
    import_folder,
    reassign_version,
    reject_candidate,
    rename_artifact,
    withdraw_relationship,
    workspace_state,
)


class EvidenceWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.incoming = self.root / "incoming"
        self.incoming.mkdir()
        self.workspace = self.root / "workspace"
        create_workspace(self.workspace, "Revenue evidence")

    def workbook(self, path, *, changed_row=None, unrelated=False, reordered=False):
        book = Workbook()
        sheet = book.active
        sheet.title = "Unrelated" if unrelated else "Revenue"
        rows = list(range(1, 31))
        if reordered:
            rows = rows[10:] + rows[:10]
        for output_row, record in enumerate(rows, 2):
            if unrelated:
                values = [f"OTHER-{record}", f"Vendor {record}", record * 1007, f"Zone {record % 7}"]
            else:
                amount = record * 100 + (25 if record == changed_row else 0)
                values = [f"INV-{record:03}", f"Customer {record}", amount, f"Region {record % 4}"]
            for column, value in enumerate(values, 1):
                sheet.cell(output_row, column, value)
        for column, value in enumerate(("Invoice", "Customer", "Amount", "Region"), 1):
            sheet.cell(1, column, value)
        sheet["F2"] = "=SUM(C2:C31)"
        sheet["F3"] = "=AVERAGE(C2:C31)"
        sheet["F4"] = "=MAX(C2:C31)"
        book.save(path)
        book.close()

    def import_version_pair(self):
        first = self.incoming / "schedule-original.xlsx"
        second = self.incoming / "client-final-renamed.xlsx"
        self.workbook(first)
        self.workbook(second, changed_row=17)
        imported = import_folder(self.workspace, self.incoming)
        state = workspace_state(self.workspace)
        candidate = next(value for value in state["candidates"] if value["status"] == "pending")
        before_blob = next(blob["id"] for blob in state["file_blobs"]
                           if blob["sha256"] == hashlib.sha256(first.read_bytes()).hexdigest())
        return imported, candidate, before_blob

    def test_many_file_import_confirmation_persistence_and_idempotence(self):
        baseline = self.incoming / "schedule-original.xlsx"
        renamed_revision = self.incoming / "client-final-renamed.xlsx"
        duplicate = self.incoming / "copy-from-email.xlsx"
        unrelated = self.incoming / "other-area.xlsx"
        self.workbook(baseline)
        self.workbook(renamed_revision, changed_row=17)
        shutil.copyfile(baseline, duplicate)
        self.workbook(unrelated, unrelated=True)
        original_hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in self.incoming.iterdir()}

        imported = import_folder(self.workspace, self.incoming)
        self.assertEqual((imported["new_blobs"], imported["exact_duplicates"]), (3, 1))
        state = workspace_state(self.workspace)
        self.assertEqual((len(state["file_blobs"]), len(state["evidence_versions"])), (3, 0))
        pending = [candidate for candidate in state["candidates"] if candidate["status"] == "pending"]
        self.assertEqual(len(pending), 1)
        candidate = pending[0]
        names = {next(blob for blob in state["file_blobs"] if blob["id"] == blob_id)["display_name"]
                 for blob_id in (candidate["left_blob_id"], candidate["right_blob_id"])}
        self.assertNotIn("other-area.xlsx", names)
        baseline_hash = original_hashes[baseline]
        before_blob = next(blob["id"] for blob in state["file_blobs"] if blob["sha256"] == baseline_hash)

        confirmed = confirm_candidate(
            self.workspace, candidate["id"], before_blob, artifact_name="Revenue Schedule")
        self.assertTrue(Path(confirmed["comparison_report"]).is_file())
        triage_report = Path(confirmed["comparison_report"]).parents[1] / "triage" / "index.html"
        self.assertTrue(triage_report.is_file())
        self.assertTrue(triage_report.with_name("triage.json").is_file())
        self.assertIn("open revision triage", (self.workspace / "index.html").read_text())
        repeated_confirmation = confirm_candidate(self.workspace, candidate["id"], before_blob)
        self.assertTrue(repeated_confirmation["existing"])
        reopened = workspace_state(self.workspace)
        self.assertEqual(len(reopened["evidence_versions"]), 2)
        self.assertEqual(reopened["artifacts"][0]["version_order"][0], confirmed["before_version_id"])
        self.assertEqual(len(reopened["comparisons"]), 1)
        content = json.loads(Path(confirmed["comparison_report"]).with_name("content.json").read_text())
        self.assertEqual(sum(block["changed_cells"] for block in content["blocks"]), 1)
        self.assertTrue(content["lineage_available"])

        repeated = import_folder(self.workspace, self.incoming)
        self.assertEqual((repeated["new_blobs"], repeated["exact_duplicates"]), (0, 4))
        repeated_state = workspace_state(self.workspace)
        self.assertEqual((len(repeated_state["file_blobs"]), len(repeated_state["candidates"])), (3, 3))
        self.assertEqual(original_hashes, {path: hashlib.sha256(path.read_bytes()).hexdigest()
                                           for path in self.incoming.iterdir()})

    def test_blob_occurrences_and_explicit_versions_have_distinct_semantics(self):
        first = self.incoming / "drop-one.xlsx"
        duplicate = self.incoming / "email-final.xlsx"
        self.workbook(first)
        shutil.copyfile(first, duplicate)
        imported = import_folder(self.workspace, self.incoming)
        state = workspace_state(self.workspace)
        self.assertEqual((imported["new_blobs"], imported["exact_duplicates"]), (1, 1))
        self.assertEqual(len(state["file_blobs"]), 1)
        self.assertEqual(len(state["file_blobs"][0]["occurrences"]), 2)
        self.assertEqual(state["evidence_versions"], [])

        blob_id = state["file_blobs"][0]["id"]
        first_version = create_logical_version(
            self.workspace, blob_id, artifact_name="Revenue Schedule", reason="Known business meaning")
        second_version = create_logical_version(
            self.workspace, blob_id, artifact_name="Tax Schedule", reason="Same bytes used with distinct meaning")
        state = workspace_state(self.workspace)
        self.assertEqual(len(state["file_blobs"]), 1)
        self.assertEqual(len(state["evidence_versions"]), 2)
        self.assertEqual({version["blob_id"] for version in state["evidence_versions"]}, {blob_id})
        self.assertEqual(len({version["artifact_id"] for version in state["evidence_versions"]}), 2)
        with self.assertRaisesRegex(ValueError, "already has"):
            reassign_version(self.workspace, first_version["version_id"],
                             artifact_id=second_version["artifact_id"], reason="Must not silently duplicate membership")
        unchanged = workspace_state(self.workspace)
        self.assertEqual(next(v for v in unchanged["evidence_versions"]
                              if v["id"] == first_version["version_id"])["artifact_id"],
                         first_version["artifact_id"])

    def test_corrections_preserve_history_and_identity(self):
        _, candidate, before_blob = self.import_version_pair()
        confirmed = confirm_candidate(
            self.workspace, candidate["id"], before_blob, artifact_name="Wrong name")
        artifact_id = confirmed["artifact_id"]
        version_ids = {confirmed["before_version_id"], confirmed["after_version_id"]}

        renamed = rename_artifact(self.workspace, artifact_id, "Revenue Schedule", "Corrected label")
        self.assertEqual((renamed["artifact_id"], renamed["new_name"]), (artifact_id, "Revenue Schedule"))
        corrected = correct_order(
            self.workspace, confirmed["relationship_id"], confirmed["after_version_id"], "Initial order was reversed")
        state = workspace_state(self.workspace)
        old = next(row for row in state["artifacts"][0]["relationships"]
                   if row["id"] == confirmed["relationship_id"])
        new = next(row for row in state["artifacts"][0]["relationships"]
                   if row["id"] == corrected["relationship_id"])
        self.assertEqual((old["status"], new["status"]), ("superseded", "active"))
        self.assertEqual(state["artifacts"][0]["version_order"][0], confirmed["after_version_id"])

        withdraw_relationship(self.workspace, corrected["relationship_id"], "Versions should not be linked")
        withdrawn = workspace_state(self.workspace)
        relationship = next(row for row in withdrawn["artifacts"][0]["relationships"]
                            if row["id"] == corrected["relationship_id"])
        self.assertEqual(relationship["status"], "withdrawn")
        self.assertEqual({v["id"] for v in withdrawn["evidence_versions"]}, version_ids)
        events = [event["event_type"] for event in withdrawn["decision_history"]]
        self.assertIn("candidate_confirmed", events)
        self.assertIn("artifact_renamed", events)
        self.assertIn("order_corrected", events)
        self.assertIn("relationship_withdrawn", events)

        reassigned = reassign_version(
            self.workspace, confirmed["after_version_id"], artifact_name="Correct artifact",
            reason="Attached to the wrong artifact")
        final = workspace_state(self.workspace)
        version = next(row for row in final["evidence_versions"] if row["id"] == confirmed["after_version_id"])
        self.assertEqual(version["artifact_id"], reassigned["to_artifact_id"])
        self.assertIn("version_reassigned", [event["event_type"] for event in final["decision_history"]])

    def test_reordered_records_use_existing_general_matcher(self):
        first = self.incoming / "first.xlsx"
        second = self.incoming / "renamed.xlsx"
        self.workbook(first)
        self.workbook(second, changed_row=8, reordered=True)
        import_folder(self.workspace, self.incoming)
        state = workspace_state(self.workspace)
        candidate = next(value for value in state["candidates"] if value["status"] == "pending")
        self.assertEqual(candidate["evidence"]["general_correspondence"]["kind"], "row_alignment")
        before_blob = next(blob["id"] for blob in state["file_blobs"] if blob["display_name"] == "first.xlsx")
        result = confirm_candidate(self.workspace, candidate["id"], before_blob, artifact_name="Moved rows")
        comparison = workspace_state(self.workspace)["comparisons"][0]
        self.assertIsNotNone(comparison["structural_report_path"])
        self.assertTrue((self.workspace / comparison["structural_report_path"]).is_file())
        self.assertTrue(Path(result["comparison_report"]).is_file())

    def test_ambiguous_proposals_and_rejection_are_persistent(self):
        for index in range(3):
            self.workbook(self.incoming / f"copy-{index}.xlsx", changed_row=10 + index)
        import_folder(self.workspace, self.incoming)
        state = workspace_state(self.workspace)
        pending = [candidate for candidate in state["candidates"] if candidate["status"] == "pending"]
        self.assertEqual(len(pending), 3)
        self.assertIn("Ambiguous", (self.workspace / "index.html").read_text())
        reject_candidate(self.workspace, pending[0]["id"])
        reopened = workspace_state(self.workspace)
        rejected = next(candidate for candidate in reopened["candidates"] if candidate["id"] == pending[0]["id"])
        self.assertEqual(rejected["status"], "rejected")
        self.assertIn("candidate_rejected", [event["event_type"] for event in reopened["decision_history"]])

    def test_workspace_create_is_safe_and_idempotent(self):
        second = create_workspace(self.workspace, "Ignored new name")
        self.assertFalse(second["created"])
        self.assertEqual((second["name"], second["schema_version"]), ("Revenue evidence", 2))
        nonempty = self.root / "not-empty"
        nonempty.mkdir()
        (nonempty / "keep.txt").write_text("keep")
        with self.assertRaisesRegex(ValueError, "empty"):
            create_workspace(nonempty)


class MissionOneMigrationTests(unittest.TestCase):
    def test_v1_workspace_migrates_without_losing_confirmed_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "workspace"
            (root / "objects").mkdir(parents=True)
            (root / "comparisons/rel_old/exact").mkdir(parents=True)
            (root / "comparisons/rel_old/exact/index.html").write_text("preserved")
            database = sqlite3.connect(root / "workspace.sqlite3")
            database.executescript("""
                CREATE TABLE workspace(id TEXT PRIMARY KEY,name TEXT NOT NULL,created_at TEXT NOT NULL);
                CREATE TABLE evidence_versions(id TEXT PRIMARY KEY,sha256 TEXT UNIQUE,extension TEXT,object_path TEXT UNIQUE,size_bytes INTEGER,first_name TEXT,first_seen_at TEXT,last_seen_at TEXT,fingerprint_json TEXT);
                CREATE TABLE occurrences(id INTEGER PRIMARY KEY,version_id TEXT,source_path TEXT,observed_name TEXT,first_seen_at TEXT,last_seen_at TEXT);
                CREATE TABLE artifacts(id TEXT PRIMARY KEY,name TEXT,created_at TEXT);
                CREATE TABLE artifact_versions(artifact_id TEXT,version_id TEXT UNIQUE,added_at TEXT);
                CREATE TABLE candidates(id TEXT PRIMARY KEY,left_version_id TEXT,right_version_id TEXT,classification TEXT,status TEXT,evidence_json TEXT,created_at TEXT,decided_at TEXT);
                CREATE TABLE version_relationships(id TEXT PRIMARY KEY,artifact_id TEXT,before_version_id TEXT,after_version_id TEXT,candidate_id TEXT,confirmed_at TEXT);
                CREATE TABLE confirmations(id TEXT PRIMARY KEY,candidate_id TEXT,decision TEXT,artifact_id TEXT,before_version_id TEXT,after_version_id TEXT,recorded_at TEXT);
                CREATE TABLE comparison_runs(id TEXT PRIMARY KEY,relationship_id TEXT UNIQUE,report_path TEXT,structural_report_path TEXT,created_at TEXT);
                PRAGMA user_version=1;
            """)
            timestamp = "2026-09-18T00:00:00+00:00"
            database.execute("INSERT INTO workspace VALUES ('ws_old','Ofgem old',?)", (timestamp,))
            database.execute("INSERT INTO artifacts VALUES ('art_old','Ofgem model',?)", (timestamp,))
            fingerprints = json.dumps({"schema_version": 1, "analyzed_name": "old.xlsx",
                                       "sheet_names": ["Sheet"], "sheets": [], "sheet_count": 1,
                                       "populated_cells": 10, "formula_cells": 1, "formula_hashes": ["f"]})
            for index, content in enumerate((b"old", b"new"), 1):
                digest = hashlib.sha256(content).hexdigest()
                version_id = f"ev_old{index}"
                object_path = f"objects/{digest}.xlsx"
                (root / object_path).write_bytes(content)
                database.execute("INSERT INTO evidence_versions VALUES (?,?,?,?,?,?,?,?,?)",
                                 (version_id, digest, ".xlsx", object_path, len(content),
                                  f"v{index}.xlsx", timestamp, timestamp, fingerprints))
                database.execute("INSERT INTO occurrences VALUES (?,?,?,?,?,?)",
                                 (index, version_id, f"/client/v{index}.xlsx", f"v{index}.xlsx", timestamp, timestamp))
                database.execute("INSERT INTO artifact_versions VALUES ('art_old',?,?)", (version_id, timestamp))
            database.execute("INSERT INTO candidates VALUES ('cand_old','ev_old1','ev_old2','likely_revision','confirmed','{}',?,?)", (timestamp, timestamp))
            database.execute("INSERT INTO version_relationships VALUES ('rel_old','art_old','ev_old1','ev_old2','cand_old',?)", (timestamp,))
            database.execute("INSERT INTO confirmations VALUES ('conf_old','cand_old','confirmed','art_old','ev_old1','ev_old2',?)", (timestamp,))
            database.execute("INSERT INTO comparison_runs VALUES ('cmp_old','rel_old','comparisons/rel_old/exact/index.html',NULL,?)", (timestamp,))
            database.commit()
            database.close()

            state = workspace_state(root)
            self.assertEqual(state["schema_version"], 2)
            self.assertEqual((len(state["file_blobs"]), len(state["evidence_versions"])), (2, 2))
            self.assertEqual(state["artifacts"][0]["version_order"], ["ev_old1", "ev_old2"])
            self.assertEqual(state["artifacts"][0]["relationships"][0]["status"], "active")
            self.assertEqual(state["decision_history"][0]["event_type"], "candidate_confirmed")
            self.assertEqual(state["comparisons"][0]["report_path"], "comparisons/rel_old/exact/index.html")
            with sqlite3.connect(root / "workspace.sqlite3") as connection:
                self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 2)
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])


if __name__ == "__main__":
    unittest.main()
