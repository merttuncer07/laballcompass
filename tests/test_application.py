import hashlib
from pathlib import Path

from openpyxl import Workbook

from workbench.application import EvidenceApplication


def _workbook(path, changed=False, formula=False):
    book = Workbook()
    sheet = book.active
    sheet.title = "Revenue"
    sheet.append(["Account", "Amount", "Calculated"])
    for row in range(2, 12):
        amount = row * 100 + (1 if changed and row == 5 else 0)
        sheet.append([f"A-{row}", amount, f"=B{row}*2"])
    if formula:
        sheet["C5"] = 1001 if changed else "=B5*2"
    book.save(path)


def _imported_application(tmp_path, formula=False):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    _workbook(evidence / "received.xlsx", formula=formula)
    _workbook(evidence / "revised.xlsx", changed=True, formula=formula)
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
              for path in evidence.iterdir()}
    application = EvidenceApplication()
    application.create_workspace(tmp_path / "workspace", "Revenue audit")
    result = application.import_folder(evidence)
    return application, evidence, hashes, result


def test_workspace_create_open_import_and_originals_unchanged(tmp_path):
    application, evidence, hashes, result = _imported_application(tmp_path)
    assert result["operation"]["new_blobs"] == 2
    assert len(application.list_unassigned_evidence()) == 2
    assert len(application.list_candidates(status="pending")) == 1
    assert hashes == {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in evidence.iterdir()}

    reopened = EvidenceApplication(tmp_path / "workspace")
    assert reopened.snapshot()["workspace"]["name"] == "Revenue audit"
    assert len(reopened.list_candidates(status="pending")) == 1


def test_candidate_rejection_persists(tmp_path):
    application, _, _, _ = _imported_application(tmp_path)
    candidate = application.list_candidates(status="pending")[0]
    application.reject_candidate(candidate["id"])
    reopened = EvidenceApplication(tmp_path / "workspace")
    assert reopened.list_candidates()[0]["status"] == "rejected"


def test_confirmed_history_and_triage_are_available_through_service(tmp_path):
    application, _, _, _ = _imported_application(tmp_path, formula=True)
    candidate = application.list_candidates(status="pending")[0]
    before_blob_id = (candidate["left_blob_id"] if candidate["left_name"] == "received.xlsx"
                      else candidate["right_blob_id"])
    confirmed = application.confirm_candidate(
        candidate["id"], before_blob_id, artifact_name="Revenue Schedule")
    relationship_id = confirmed["operation"]["relationship_id"]

    versions = application.list_versions(confirmed["operation"]["artifact_id"])
    assert [row["version_number"] for row in versions] == [1, 2]
    triage = application.get_revision_triage(relationship_id)
    assert triage["summary"]["triage_group_count"] >= 1
    assert "dependency_coverage" in triage
    assert "formula_to_literal" in {row["category"] for row in triage["groups"]}
    group = application.get_triage_group(relationship_id, triage["groups"][0]["id"])
    assert group["id"] == triage["groups"][0]["id"]


def test_correction_operations_flow_through_service(tmp_path):
    application, _, _, _ = _imported_application(tmp_path)
    candidate = application.list_candidates(status="pending")[0]
    result = application.confirm_candidate(
        candidate["id"], candidate["left_blob_id"], artifact_name="Old name")
    artifact_id = result["operation"]["artifact_id"]
    relationship_id = result["operation"]["relationship_id"]
    application.rename_artifact(artifact_id, "Revenue", "Corrected naming")
    relationship = next(row for row in application.snapshot()["relationships"]
                        if row["id"] == relationship_id)
    reversed_result = application.correct_version_order(
        relationship_id, relationship["after_version_id"], "Client clarified chronology")
    application.withdraw_relationship(
        reversed_result["operation"]["relationship_id"], "Relationship was mistaken")
    state = EvidenceApplication(tmp_path / "workspace").snapshot()
    assert state["artifacts"][0]["name"] == "Revenue"
    assert not any(row["status"] == "active" for row in state["relationships"])
