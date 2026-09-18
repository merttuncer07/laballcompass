import importlib

from PySide6.QtWidgets import QApplication, QLabel

from desktop.app import build_application


def test_desktop_modules_do_not_depend_on_browser_engines():
    for name in ("desktop.app", "desktop.main_window", "workbench.application"):
        module = importlib.import_module(name)
        source = open(module.__file__, encoding="utf-8").read()
        assert "webbrowser" not in source
        assert "QtWebEngine" not in source


def test_desktop_changed_since_use_copy_does_not_make_audit_conclusions():
    source = open(importlib.import_module("desktop.main_window").__file__,
                  encoding="utf-8").read().lower()
    for prohibited in ("redo testing", "workpaper failed", "audit work invalid",
                       "audit work is wrong", "workpaper is stale"):
        assert prohibited not in source
    assert "evidence changed since use" in source


def test_application_starts_headlessly_without_workspace(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    application, window = build_application()
    assert isinstance(application, QApplication)
    assert window.centralWidget().count() == 3
    assert window.windowTitle() == "Audit Evidence Workspace"
    assert window.findChild(QLabel, "structuralDriftSnapshot") is not None
    window.close()
