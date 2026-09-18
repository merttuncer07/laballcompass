import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from openpyxl import Workbook
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from desktop.background_jobs import BackgroundJobRunner
from desktop.main_window import AuditMainWindow
from workbench.application import EvidenceApplication
import workbench.evidence_workspace as evidence_workspace


def _application():
    return QApplication.instance() or QApplication(["desktop-job-test"])


def _wait_until(predicate, timeout=5):
    application = _application()
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        application.processEvents()
        time.sleep(0.005)
    application.processEvents()
    assert predicate()


def _workbook(path, changed=False):
    book = Workbook()
    sheet = book.active
    sheet.title = "Revenue"
    sheet.append(["Account", "Amount", "Calculated"])
    for row in range(2, 12):
        sheet.append([f"A-{row}", row * 100 + (1 if changed and row == 5 else 0),
                      f"=B{row}*2"])
    book.save(path)


def _evidence_pair(root):
    root.mkdir()
    _workbook(root / "received.xlsx")
    _workbook(root / "revised.xlsx", changed=True)


def test_controlled_slow_job_keeps_event_loop_alive_and_rejects_duplicate():
    runner = BackgroundJobRunner()
    heartbeat = []
    results = []
    runner.succeeded.connect(results.append)
    QTimer.singleShot(20, lambda: heartbeat.append("event-loop-responsive"))

    assert runner.start(lambda: (time.sleep(0.15), "complete")[1], "Working…")
    assert not runner.start(lambda: "duplicate", "Duplicate")
    _wait_until(lambda: not runner.is_busy)

    assert heartbeat == ["event-loop-responsive"]
    assert results == ["complete"]


def test_successful_background_import_updates_ui_and_survives_restart(tmp_path):
    _application()
    workspace = tmp_path / "workspace"
    evidence = tmp_path / "evidence"
    _evidence_pair(evidence)
    service = EvidenceApplication()
    service.create_workspace(workspace, "Pilot")
    window = AuditMainWindow(service, debug_log_path=tmp_path / "debug.log")

    window._run(lambda: service.import_folder(evidence),
                busy="Importing and analyzing evidence…",
                success="Evidence import complete")
    assert not window.job_progress.isHidden()
    assert not window.evidence_tree.isEnabled()
    _wait_until(lambda: not window.jobs.is_busy)

    assert window.evidence_tree.isEnabled()
    assert window.job_progress.isHidden()
    assert len(window._snapshot["candidates"]) == 1
    reopened = EvidenceApplication(workspace)
    assert len(reopened.list_candidates()) == 1
    window.close()


def test_failed_background_import_rolls_back_and_keeps_debug_detail(
        tmp_path, monkeypatch):
    _application()
    workspace = tmp_path / "workspace"
    evidence = tmp_path / "evidence"
    debug_log = tmp_path / "desktop-debug.log"
    _evidence_pair(evidence)
    service = EvidenceApplication()
    service.create_workspace(workspace, "Pilot")
    before = service.snapshot()
    window = AuditMainWindow(service, debug_log_path=debug_log)
    messages = []
    monkeypatch.setattr(
        QMessageBox, "critical",
        lambda _parent, _title, message: messages.append(message))

    def fail_candidate_analysis(*_args, **_kwargs):
        raise RuntimeError("controlled candidate failure detail")

    monkeypatch.setattr(evidence_workspace, "_candidate_evidence", fail_candidate_analysis)
    window._run(lambda: service.import_folder(evidence),
                busy="Importing and analyzing evidence…")
    _wait_until(lambda: not window.jobs.is_busy)

    reopened = EvidenceApplication(workspace)
    assert reopened.snapshot() == before
    assert messages and "operation failed" in messages[0].lower()
    assert "controlled candidate failure detail" not in messages[0]
    assert "controlled candidate failure detail" in debug_log.read_text(encoding="utf-8")
    assert not list((workspace / "comparisons").iterdir())
    window.close()
