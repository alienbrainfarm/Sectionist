"""Shared pytest configuration for the Sectionist frontend tests."""

import os
import sys
from pathlib import Path

import pytest

# The GUI tests must never try to open a real window: CI has no display server.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

FRONTEND_DIR = Path(__file__).parent
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))


@pytest.fixture(scope="session")
def qapp():
    """Provide a single QApplication for the whole test session."""
    from PyQt6.QtWidgets import QApplication

    import tempfile

    from PyQt6.QtCore import QSettings

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    # Preferences the app remembers (QSettings) go to a throwaway folder,
    # never the developer's real settings.
    app.setOrganizationName("SectionistTests")
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, tempfile.mkdtemp()
    )
    yield app


@pytest.fixture(autouse=True)
def delete_windows():
    """Shut down and delete every window a test made.

    close() only hides a window: its timers, threads and controllers stay
    alive in C++. Left to pile up across the suite they crashed Qt (a
    segfault on macOS once enough window tests had run).
    """
    yield
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        return
    from PyQt6.QtCore import QCoreApplication, QEvent

    # Deliver anything still queued (a worker's result, say) while its
    # receivers exist, then shut down and delete.
    app.processEvents()
    for widget in app.topLevelWidgets():
        shutdown = getattr(widget, "shutdown", None)
        if callable(shutdown):
            shutdown()
        widget.close()
        widget.deleteLater()
    app.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
