from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFileDialog, QFormLayout, QHBoxLayout,
    QInputDialog, QLabel, QMainWindow, QMessageBox, QPushButton, QSplitter,
    QPlainTextEdit, QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
    QWidget,
)

from workbench.application import EvidenceApplication


ROLE_KIND = Qt.ItemDataRole.UserRole
ROLE_ID = Qt.ItemDataRole.UserRole + 1


class AuditMainWindow(QMainWindow):
    def __init__(self, application=None):
        super().__init__()
        self.application = application or EvidenceApplication()
        self._snapshot = None
        self._triage = None
        self._relationship_id = None
        self.setWindowTitle("Audit Evidence Workspace")
        self.resize(1440, 850)
        self._build_ui()
        if self.application.workspace_path:
            self.refresh()

    def _build_ui(self):
        toolbar = self.addToolBar("Workspace")
        toolbar.setMovable(False)
        for text, callback in (("Create Workspace", self.create_workspace),
                               ("Open Workspace", self.open_workspace),
                               ("Import Folder", self.import_folder)):
            action = toolbar.addAction(text)
            action.triggered.connect(callback)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._left_pane())
        splitter.addWidget(self._center_pane())
        splitter.addWidget(self._right_pane())
        splitter.setSizes([380, 610, 450])
        self.setCentralWidget(splitter)
        self.statusBar().showMessage("Create or open an evidence workspace")

    def _left_pane(self):
        pane = QWidget(objectName="evidencePane")
        layout = QVBoxLayout(pane)
        layout.addWidget(QLabel("Evidence & versions"))
        self.evidence_tree = QTreeWidget()
        self.evidence_tree.setHeaderLabels(["Item", "State"])
        self.evidence_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.evidence_tree.customContextMenuRequested.connect(self._show_context_menu)
        self.evidence_tree.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self.evidence_tree)
        self.candidate_explanation = QLabel("Select a revision candidate to see why it was proposed.")
        self.candidate_explanation.setWordWrap(True)
        layout.addWidget(self.candidate_explanation)
        buttons = QHBoxLayout()
        self.confirm_button = QPushButton("Confirm")
        self.reject_button = QPushButton("Reject")
        self.confirm_button.clicked.connect(self.confirm_selected_candidate)
        self.reject_button.clicked.connect(self.reject_selected_candidate)
        buttons.addWidget(self.confirm_button); buttons.addWidget(self.reject_button)
        layout.addLayout(buttons)
        return pane

    def _center_pane(self):
        pane = QWidget(objectName="triagePane")
        layout = QVBoxLayout(pane)
        self.revision_title = QLabel("Revision Triage")
        layout.addWidget(self.revision_title)
        self.summary_label = QLabel("Select an adjacent confirmed revision pair.")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Type"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("All change types", None)
        self.type_filter.currentIndexChanged.connect(self._populate_groups)
        controls.addWidget(self.type_filter)
        controls.addWidget(QLabel("Sort"))
        self.sort_filter = QComboBox()
        self.sort_filter.addItems(["Structural reach", "Location", "Change type"])
        self.sort_filter.currentIndexChanged.connect(self._populate_groups)
        controls.addWidget(self.sort_filter)
        layout.addLayout(controls)
        self.group_table = QTableWidget(0, 5)
        self.group_table.setHorizontalHeaderLabels(
            ["Type", "Location", "Raw", "Resolved reach", "Coverage"])
        self.group_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.group_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.group_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.group_table.verticalHeader().setVisible(False)
        self.group_table.itemSelectionChanged.connect(self._group_selected)
        self.group_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.group_table)
        return pane

    def _right_pane(self):
        pane = QWidget(objectName="detailsPane")
        layout = QVBoxLayout(pane)
        layout.addWidget(QLabel("Group details"))
        form = QFormLayout()
        self.detail_labels = {}
        for key, title in (("type", "Type"), ("before", "Before region"),
                           ("after", "After region"), ("raw", "Raw changes"),
                           ("transition", "Formula transition"),
                           ("movement", "Movement evidence"),
                           ("reach", "Resolved structural reach"),
                           ("coverage", "Dependency coverage")):
            label = QLabel("—")
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            form.addRow(title, label)
            self.detail_labels[key] = label
        layout.addLayout(form)
        layout.addWidget(QLabel("Representative before / after"))
        self.observation_table = QTableWidget(0, 4)
        self.observation_table.setHorizontalHeaderLabels(["Before", "Value", "After", "Value"])
        self.observation_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.observation_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.observation_table)
        self.targets_label = QPlainTextEdit("Resolved downstream targets: —")
        self.targets_label.setReadOnly(True)
        self.targets_label.setMaximumHeight(150)
        layout.addWidget(self.targets_label)
        return pane

    def create_workspace(self):
        path = QFileDialog.getExistingDirectory(self, "Choose an empty workspace folder")
        if not path: return
        name, accepted = QInputDialog.getText(self, "Workspace name", "Name")
        if accepted:
            self._run(lambda: self.application.create_workspace(path, name or None))

    def open_workspace(self):
        path = QFileDialog.getExistingDirectory(self, "Open evidence workspace")
        if path:
            self._run(lambda: self.application.open_workspace(path))

    def import_folder(self):
        if not self.application.workspace_path:
            return self._error(ValueError("Create or open a workspace first"))
        path = QFileDialog.getExistingDirectory(self, "Import workbook folder")
        if path:
            self._run(lambda: self.application.import_folder(path), busy="Analyzing evidence…")

    def refresh(self):
        self._snapshot = self.application.snapshot()
        self.evidence_tree.clear()
        artifacts = QTreeWidgetItem(["Artifacts", str(len(self._snapshot["artifacts"]))])
        self.evidence_tree.addTopLevelItem(artifacts)
        for artifact in self._snapshot["artifacts"]:
            item = self._tree_item(artifact["name"], "artifact", artifact["id"])
            item.setText(1, f'{len(artifact["versions"])} version(s)')
            artifacts.addChild(item)
            relationship_by_after = {row["after_version_id"]: row for row in artifact["relationships"]
                                     if row["status"] == "active"}
            for version in artifact["versions"]:
                version_item = self._tree_item(
                    f'v{version["version_number"]}  {version["display_name"]}',
                    "version", version["id"])
                version_item.setText(1, version["sha256"][:10] + "…")
                item.addChild(version_item)
                relationship = relationship_by_after.get(version["id"])
                if relationship:
                    revision = self._tree_item(
                        f'Compare previous → v{version["version_number"]}',
                        "relationship", relationship["id"])
                    revision.setText(1, "triage")
                    version_item.addChild(revision)
        unassigned = QTreeWidgetItem(["Unassigned evidence", str(len(self._snapshot["unassigned_evidence"]))])
        self.evidence_tree.addTopLevelItem(unassigned)
        for blob in self._snapshot["unassigned_evidence"]:
            item = self._tree_item(blob["display_name"], "blob", blob["id"])
            item.setText(1, blob["sha256"][:10] + "…")
            unassigned.addChild(item)
        pending = [row for row in self._snapshot["candidates"] if row["status"] == "pending"]
        candidates = QTreeWidgetItem(["Revision candidates", str(len(pending))])
        self.evidence_tree.addTopLevelItem(candidates)
        for row in pending:
            item = self._tree_item(f'{row["left_name"]} ↔ {row["right_name"]}', "candidate", row["id"])
            item.setText(1, row["classification"])
            candidates.addChild(item)
        for node in (artifacts, unassigned, candidates): node.setExpanded(True)
        self.setWindowTitle(f'Audit Evidence Workspace — {self._snapshot["workspace"]["name"]}')
        self.statusBar().showMessage(self._snapshot["workspace_path"])

    @staticmethod
    def _tree_item(text, kind, item_id):
        item = QTreeWidgetItem([text, ""])
        item.setData(0, ROLE_KIND, kind); item.setData(0, ROLE_ID, item_id)
        return item

    def _selection_changed(self):
        item = self.evidence_tree.currentItem()
        kind = item.data(0, ROLE_KIND) if item else None
        item_id = item.data(0, ROLE_ID) if item else None
        self.confirm_button.setEnabled(kind == "candidate")
        self.reject_button.setEnabled(kind == "candidate")
        if kind == "candidate":
            row = next(row for row in self._snapshot["candidates"] if row["id"] == item_id)
            evidence = row["evidence"]
            structure = evidence.get("structure", {})
            reasons = " ".join(evidence.get("reasons", []))
            self.candidate_explanation.setText(
                f'Sheet overlap {structure.get("sheet_name_overlap", 0):.0%}; '
                f'cell-count correspondence {structure.get("populated_cell_count_ratio", 0):.0%}; '
                f'common formula texts {structure.get("common_formula_text_hashes", 0)}. {reasons}')
        elif kind == "relationship":
            self._load_triage(item_id)

    def _load_triage(self, relationship_id):
        try:
            self._triage = self.application.get_revision_triage(relationship_id)
        except (ValueError, OSError, json.JSONDecodeError) as error:
            return self._error(error)
        self._relationship_id = relationship_id
        relation = self._triage["relationship"]
        self.revision_title.setText(
            f'{self._version_label(relation["before_version_id"])} → '
            f'{self._version_label(relation["after_version_id"])}')
        summary, coverage = self._triage["summary"], self._triage["dependency_coverage"]
        self.summary_label.setText(
            f'{summary["raw_change_count"]:,} raw changes → {summary["triage_group_count"]:,} groups '
            f'({summary["compression_ratio"]:.2f}× compression). '
            f'Dependency resolution: {coverage.get("resolved_formula_count", 0):,} of '
            f'{coverage.get("formula_count", 0):,} formulas.')
        types = sorted({row["category"] for row in self._triage["groups"]})
        self.type_filter.blockSignals(True); self.type_filter.clear()
        self.type_filter.addItem("All change types", None)
        for value in types: self.type_filter.addItem(value.replace("_", " ").title(), value)
        self.type_filter.blockSignals(False)
        self._populate_groups()

    def _version_label(self, version_id):
        for artifact in self._snapshot["artifacts"]:
            for version in artifact["versions"]:
                if version["id"] == version_id:
                    return f'{artifact["name"]} v{version["version_number"]}'
        return version_id

    def _populate_groups(self):
        groups = list(self._triage["groups"]) if self._triage else []
        selected_type = self.type_filter.currentData()
        if selected_type: groups = [row for row in groups if row["category"] == selected_type]
        sort = self.sort_filter.currentText()
        if sort == "Location": groups.sort(key=lambda row: (row["sheet"], row.get("left_range") or ""))
        elif sort == "Change type": groups.sort(key=lambda row: (row["category"], row["sheet"]))
        else: groups.sort(key=lambda row: (-row["resolved_downstream_target_count"], row["sheet"]))
        self.group_table.setRowCount(len(groups))
        for index, group in enumerate(groups):
            location = f'{group["sheet"]} · {group.get("left_range") or "—"}'
            coverage = "Incomplete" if self._coverage_incomplete(group) else "Resolved"
            values = [group["category"].replace("_", " ").title(), location,
                      str(group["changed_cell_count"]),
                      str(group["resolved_downstream_target_count"]), coverage]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(ROLE_ID, group["id"])
                self.group_table.setItem(index, column, item)

    def _coverage_incomplete(self, group):
        coverage = self._triage.get("dependency_coverage", {}) if self._triage else {}
        return (group.get("unresolved_coverage", False) or
                not coverage.get("lineage_available", False) or
                bool(coverage.get("unresolved_formula_count", 0)))

    def _group_selected(self):
        items = self.group_table.selectedItems()
        if not items: return
        group_id = items[0].data(ROLE_ID)
        group = next(row for row in self._triage["groups"] if row["id"] == group_id)
        self.detail_labels["type"].setText(group["category"].replace("_", " ").title())
        self.detail_labels["before"].setText(f'{group["sheet"]}!{group.get("left_range") or "—"}')
        self.detail_labels["after"].setText(f'{group.get("right_sheet") or group["sheet"]}!{group.get("right_range") or "—"}')
        self.detail_labels["raw"].setText(str(group["changed_cell_count"]))
        self.detail_labels["transition"].setText(group.get("formula_transition") or "—")
        movement = group.get("movement_evidence") or {}
        self.detail_labels["movement"].setText(
            "Detected" + (f' ({movement.get("matching_rows", 0)} matching rows)' if movement else "")
            if group.get("structural_movement_detected") else "—")
        self.detail_labels["reach"].setText(str(group["resolved_downstream_target_count"]))
        coverage = self._triage.get("dependency_coverage", {})
        if self._coverage_incomplete(group):
            coverage_text = ("Incomplete — resolved reach is not exhaustive. "
                             f'{coverage.get("unresolved_formula_count", "unknown")} workbook formulas unresolved.')
        else:
            coverage_text = "Complete for supported formula graph"
        self.detail_labels["coverage"].setText(coverage_text)
        observations = group.get("representative_observations", [])
        self.observation_table.setRowCount(len(observations))
        for row_index, observation in enumerate(observations):
            values = [observation.get("left"), observation.get("left_value"),
                      observation.get("right"), observation.get("right_value")]
            for column, value in enumerate(values):
                self.observation_table.setItem(row_index, column, QTableWidgetItem(str(value or "")))
        targets = group.get("resolved_downstream_targets", [])
        self.targets_label.setPlainText(
            "Resolved downstream targets:\n" + ("\n".join(targets) or "0"))

    def confirm_selected_candidate(self):
        item = self.evidence_tree.currentItem()
        if not item or item.data(0, ROLE_KIND) != "candidate": return
        candidate = next(row for row in self._snapshot["candidates"] if row["id"] == item.data(0, ROLE_ID))
        choices = [candidate["left_name"], candidate["right_name"]]
        before_name, accepted = QInputDialog.getItem(
            self, "Revision order", "Which file came first?", choices, 0, False)
        if not accepted: return
        before_id = (candidate["left_blob_id"] if before_name == candidate["left_name"]
                     else candidate["right_blob_id"])
        artifact_choices = [row["name"] for row in self._snapshot["artifacts"]] + ["Create new artifact…"]
        choice, accepted = QInputDialog.getItem(
            self, "Evidence artifact", "Attach to", artifact_choices, 0, False)
        if not accepted: return
        kwargs = {}
        if choice == "Create new artifact…":
            name, accepted = QInputDialog.getText(self, "New artifact", "Artifact name")
            if not accepted or not name.strip(): return
            kwargs["artifact_name"] = name.strip()
        else:
            kwargs["artifact_id"] = next(row["id"] for row in self._snapshot["artifacts"] if row["name"] == choice)
        self._run(lambda: self.application.confirm_candidate(
            candidate["id"], before_id, **kwargs), busy="Building revision triage…")

    def reject_selected_candidate(self):
        item = self.evidence_tree.currentItem()
        if not item or item.data(0, ROLE_KIND) != "candidate": return
        if QMessageBox.question(self, "Reject candidate", "Preserve this pair as rejected?") == QMessageBox.StandardButton.Yes:
            self._run(lambda: self.application.reject_candidate(item.data(0, ROLE_ID)))

    def _show_context_menu(self, point):
        from PySide6.QtWidgets import QMenu
        item = self.evidence_tree.itemAt(point)
        if not item: return
        kind, item_id = item.data(0, ROLE_KIND), item.data(0, ROLE_ID)
        menu = QMenu(self)
        if kind == "artifact":
            menu.addAction("Rename artifact", lambda: self._rename_artifact(item_id))
        elif kind == "relationship":
            menu.addAction("Withdraw relationship", lambda: self._withdraw_relationship(item_id))
            menu.addAction("Reverse version order", lambda: self._reverse_order(item_id))
        elif kind == "version":
            menu.addAction("Reassign version", lambda: self._reassign_version(item_id))
        if not menu.isEmpty(): menu.exec(self.evidence_tree.viewport().mapToGlobal(point))

    def _reason(self, title):
        value, accepted = QInputDialog.getText(self, title, "Reason (kept in decision history)")
        return value.strip() if accepted else ""

    def _rename_artifact(self, artifact_id):
        name, accepted = QInputDialog.getText(self, "Rename artifact", "New name")
        reason = self._reason("Rename reason") if accepted and name.strip() else ""
        if reason: self._run(lambda: self.application.rename_artifact(artifact_id, name, reason))

    def _withdraw_relationship(self, relationship_id):
        reason = self._reason("Withdraw relationship")
        if reason: self._run(lambda: self.application.withdraw_relationship(relationship_id, reason))

    def _reverse_order(self, relationship_id):
        relation = next(row for row in self._snapshot["relationships"] if row["id"] == relationship_id)
        reason = self._reason("Correct ordering")
        if reason:
            self._run(lambda: self.application.correct_version_order(
                relationship_id, relation["after_version_id"], reason), busy="Rebuilding revision triage…")

    def _reassign_version(self, version_id):
        artifacts = [row for row in self._snapshot["artifacts"]
                     if all(version["id"] != version_id for version in row["versions"])]
        choices = [row["name"] for row in artifacts] + ["Create new artifact…"]
        if not choices: return
        choice, accepted = QInputDialog.getItem(self, "Reassign version", "Target artifact", choices, 0, False)
        if not accepted: return
        reason = self._reason("Reassignment reason")
        if not reason: return
        if choice == "Create new artifact…":
            name, accepted = QInputDialog.getText(self, "New artifact", "Artifact name")
            if accepted and name.strip():
                self._run(lambda: self.application.reassign_version(
                    version_id, artifact_name=name.strip(), reason=reason))
        else:
            target = next(row["id"] for row in artifacts if row["name"] == choice)
            self._run(lambda: self.application.reassign_version(
                version_id, artifact_id=target, reason=reason))

    def _run(self, operation, busy=None):
        if busy: self.statusBar().showMessage(busy)
        try:
            operation()
            self.refresh()
        except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
            self._error(error)

    def _error(self, error):
        QMessageBox.critical(self, "Audit Evidence Workspace", str(error))
        self.statusBar().showMessage(str(error))
