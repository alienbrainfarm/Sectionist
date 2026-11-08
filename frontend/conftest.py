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

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
