import importlib

from PySide6.QtWidgets import QApplication

from desktop.app import build_application


def test_desktop_modules_do_not_depend_on_browser_engines():
    for name in ("desktop.app", "desktop.main_window", "workbench.application"):
        module = importlib.import_module(name)
        source = open(module.__file__, encoding="utf-8").read()
        assert "webbrowser" not in source
        assert "QtWebEngine" not in source


def test_application_starts_headlessly_without_workspace(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    application, window = build_application()
    assert isinstance(application, QApplication)
    assert window.centralWidget().count() == 3
    assert window.windowTitle() == "Audit Evidence Workspace"
    window.close()
