"""Application boundary for the local evidence-version desktop product.

The desktop layer consumes this module only.  Persistence, workbook parsing,
candidate assessment and revision triage remain owned by the existing domain
modules.
"""
from __future__ import annotations

import json
from pathlib import Path

from .evidence_workspace import (
    confirm_candidate as _confirm_candidate,
    correct_order as _correct_order,
    create_workspace as _create_workspace,
    import_folder as _import_folder,
    reassign_version as _reassign_version,
    reject_candidate as _reject_candidate,
    rename_artifact as _rename_artifact,
    withdraw_relationship as _withdraw_relationship,
    workspace_state,
)


class EvidenceApplication:
    """Stateful orchestration API for one open local workspace."""

    def __init__(self, workspace=None):
        self._workspace: Path | None = None
        if workspace is not None:
            self.open_workspace(workspace)

    @property
    def workspace_path(self):
        return self._workspace

    def _require_workspace(self):
        if self._workspace is None:
            raise ValueError("Create or open a workspace first")
        return self._workspace

    def create_workspace(self, path, name=None):
        result = _create_workspace(path, name)
        self._workspace = Path(result["workspace"])
        return self.snapshot()

    def open_workspace(self, path):
        root = Path(path).expanduser().resolve()
        state = workspace_state(root)
        self._workspace = root
        return self._view(state)

    def import_folder(self, folder):
        result = _import_folder(self._require_workspace(), folder)
        return {"operation": result, "workspace": self.snapshot()}

    def snapshot(self):
        return self._view(workspace_state(self._require_workspace()))

    def list_artifacts(self):
        return self.snapshot()["artifacts"]

    def list_versions(self, artifact_id):
        artifact = self._by_id(self.list_artifacts(), artifact_id, "artifact")
        return artifact["versions"]

    def list_candidates(self, status=None):
        candidates = self.snapshot()["candidates"]
        return [row for row in candidates if status is None or row["status"] == status]

    def list_unassigned_evidence(self):
        return self.snapshot()["unassigned_evidence"]

    def confirm_candidate(self, candidate_id, before_blob_id, *, artifact_id=None,
                          artifact_name=None, override_no_match=False):
        result = _confirm_candidate(
            self._require_workspace(), candidate_id, before_blob_id,
            artifact_name=artifact_name, artifact_id=artifact_id,
            override_no_match=override_no_match,
        )
        return {"operation": result, "workspace": self.snapshot()}

    def reject_candidate(self, candidate_id):
        result = _reject_candidate(self._require_workspace(), candidate_id)
        return {"operation": result, "workspace": self.snapshot()}

    def get_revision_triage(self, relationship_id):
        snapshot = self.snapshot()
        relationship = self._by_id(snapshot["relationships"], relationship_id, "relationship")
        if relationship["status"] != "active":
            raise ValueError("Revision triage is available only for an active relationship")
        comparison = next(
            (row for row in snapshot["comparisons"] if row["relationship_id"] == relationship_id),
            None,
        )
        if comparison is None:
            raise ValueError("This revision has no completed comparison")
        triage_path = (self._require_workspace() / "comparisons" / relationship_id /
                       "triage" / "triage.json")
        if not triage_path.is_file():
            raise ValueError("This revision has no completed triage")
        result = json.loads(triage_path.read_text(encoding="utf-8"))
        result["relationship"] = relationship
        return result

    def get_triage_group(self, relationship_id, group_id):
        triage = self.get_revision_triage(relationship_id)
        return self._by_id(triage["groups"], group_id, "triage group")

    def rename_artifact(self, artifact_id, name, reason):
        result = _rename_artifact(self._require_workspace(), artifact_id, name, reason)
        return {"operation": result, "workspace": self.snapshot()}

    def withdraw_relationship(self, relationship_id, reason):
        result = _withdraw_relationship(self._require_workspace(), relationship_id, reason)
        return {"operation": result, "workspace": self.snapshot()}

    def reassign_version(self, version_id, *, artifact_id=None, artifact_name=None, reason):
        result = _reassign_version(
            self._require_workspace(), version_id, artifact_id=artifact_id,
            artifact_name=artifact_name, reason=reason,
        )
        return {"operation": result, "workspace": self.snapshot()}

    def correct_version_order(self, relationship_id, before_version_id, reason):
        result = _correct_order(
            self._require_workspace(), relationship_id, before_version_id, reason,
        )
        return {"operation": result, "workspace": self.snapshot()}

    @staticmethod
    def _by_id(rows, item_id, label):
        row = next((item for item in rows if item["id"] == item_id), None)
        if row is None:
            raise ValueError(f"Unknown {label} ID")
        return row

    @staticmethod
    def _view(state):
        blobs = {row["id"]: row for row in state["file_blobs"]}
        versions = {row["id"]: row for row in state["evidence_versions"]}

        artifacts = []
        relationships = []
        for source in state["artifacts"]:
            artifact = {key: value for key, value in source.items()
                        if key not in ("version_order", "relationships")}
            artifact_versions = []
            for number, version_id in enumerate(source["version_order"], 1):
                version = dict(versions[version_id])
                blob = blobs[version["blob_id"]]
                version.update({
                    "version_number": number,
                    "display_name": blob["display_name"],
                    "sha256": blob["sha256"],
                    "size_bytes": blob["size_bytes"],
                })
                artifact_versions.append(version)
            artifact["versions"] = artifact_versions
            artifact["ordering_ambiguous"] = source["ordering_ambiguous"]
            artifact["relationships"] = [dict(row) for row in source["relationships"]]
            artifacts.append(artifact)
            relationships.extend(artifact["relationships"])

        candidates = []
        for source in state["candidates"]:
            row = dict(source)
            left, right = blobs[row["left_blob_id"]], blobs[row["right_blob_id"]]
            row["left_name"] = left["display_name"]
            row["right_name"] = right["display_name"]
            candidates.append(row)

        unassigned = []
        for blob in state["file_blobs"]:
            if not blob["version_ids"]:
                unassigned.append({
                    "id": blob["id"], "display_name": blob["display_name"],
                    "sha256": blob["sha256"], "size_bytes": blob["size_bytes"],
                    "occurrences": blob["occurrences"],
                })

        return {
            "schema_version": state["schema_version"],
            "workspace_path": state["workspace_path"],
            "workspace": state["workspace"],
            "artifacts": artifacts,
            "unassigned_evidence": unassigned,
            "candidates": candidates,
            "relationships": relationships,
            "comparisons": state["comparisons"],
            "decision_history": state["decision_history"],
        }
