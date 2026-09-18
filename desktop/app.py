from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from workbench.application import EvidenceApplication
from .main_window import AuditMainWindow


def build_application(workspace=None):
    qt_application = QApplication.instance() or QApplication(sys.argv[:1])
    qt_application.setOrganizationName("Audit Evidence Workspace")
    qt_application.setApplicationName("Audit Evidence Workspace")
    service = EvidenceApplication(workspace) if workspace else EvidenceApplication()
    window = AuditMainWindow(service)
    return qt_application, window


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local audit evidence desktop application")
    parser.add_argument("--workspace", help="Open an existing evidence workspace")
    args = parser.parse_args(argv)
    application, window = build_application(args.workspace)
    window.show()
    return application.exec()
