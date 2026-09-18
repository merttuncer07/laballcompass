"""Single-flight background execution for the native desktop application."""
from __future__ import annotations

import json
import traceback

from PySide6.QtCore import QObject, QThread, Signal, Slot


class _OperationWorker(QObject):
    succeeded = Signal(object)
    failed = Signal(str, str)
    completed = Signal()

    def __init__(self, operation):
        super().__init__()
        self._operation = operation

    @Slot()
    def run(self):
        try:
            result = self._operation()
        except Exception as error:  # The traceback is retained outside the UI message.
            if isinstance(error, (ValueError, OSError, KeyError, json.JSONDecodeError)):
                summary = str(error) or type(error).__name__
            else:
                summary = "The operation failed. The workspace was not updated."
            self.failed.emit(summary, traceback.format_exc())
        else:
            self.succeeded.emit(result)
        finally:
            self.completed.emit()


class BackgroundJobRunner(QObject):
    """Run one operation at a time without blocking the Qt event loop."""

    started = Signal(str)
    succeeded = Signal(object)
    failed = Signal(str, str)
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._worker = None

    @property
    def is_busy(self):
        return self._thread is not None

    def start(self, operation, status):
        if self.is_busy:
            return False
        thread = QThread(self)
        worker = _OperationWorker(operation)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(self.succeeded)
        worker.failed.connect(self.failed)
        worker.completed.connect(thread.quit)
        worker.completed.connect(worker.deleteLater)
        thread.finished.connect(lambda: self._thread_finished(thread))
        self._thread = thread
        self._worker = worker
        self.started.emit(status)
        thread.start()
        return True

    def _thread_finished(self, thread):
        if self._thread is thread:
            self._thread = None
            self._worker = None
        thread.deleteLater()
        self.finished.emit()
