"""Structural tests for the PyQt6 frontend.

These replace an earlier set of checks that returned True/False instead of
asserting, which meant they could never fail. Everything here is a real
assertion.
"""

import ast
from pathlib import Path

FRONTEND_DIR = Path(__file__).parent

REQUIRED_MODULES = [
    "analysis_worker.py",
    "audio_player.py",
    "timeline_widget.py",
    "main_window.py",
]


def test_required_modules_exist():
    missing = [name for name in REQUIRED_MODULES if not (FRONTEND_DIR / name).exists()]
    assert missing == [], f"missing frontend modules: {missing}"


def test_modules_expose_expected_classes():
    from PyQt6.QtCore import QThread
    from PyQt6.QtWidgets import QMainWindow, QWidget

    from analysis_worker import AnalysisWorker
    from audio_player import AudioPlayer
    from main_window import SectionistMainWindow
    from timeline_widget import TimelineWidget

    assert issubclass(AnalysisWorker, QThread)
    assert issubclass(TimelineWidget, QWidget)
    assert issubclass(SectionistMainWindow, QMainWindow)
    assert callable(AudioPlayer.load_file)


def test_entry_point_delegates_to_main_window():
    source = (FRONTEND_DIR / "sectionist_gui.py").read_text()
    tree = ast.parse(source)

    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "main" in function_names
    assert "SectionistMainWindow" in source
    assert 'if __name__ == "__main__":' in source


def test_main_window_builds_expected_widgets(qapp):
    from main_window import SectionistMainWindow

    window = SectionistMainWindow()
    try:
        assert "Sectionist" in window.windowTitle()
        assert window.timeline is not None
        assert window.sections_text is not None
        assert window.details_text is not None
        # Nothing has been analysed yet, so saving stays disabled.
        assert window.save_action.isEnabled() is False
    finally:
        window.close()


def test_display_results_populates_panels_and_timeline(qapp):
    from main_window import SectionistMainWindow

    payload = {
        "success": True,
        "file_name": "song.wav",
        "analysis": {
            "duration": 60.0,
            "tempo": 120.0,
            "key": "C major",
            "key_changes": [
                {"timestamp": 30.0, "from_key": "C major", "to_key": "G major"}
            ],
            "sections": [
                {"name": "Intro", "start": 0.0, "end": 20.0, "confidence": 0.9},
                {"name": "Verse 1", "start": 20.0, "end": 60.0, "confidence": 0.7},
            ],
            "beats_detected": 120,
            "chords": [{"name": "C", "start": 0.0, "end": 4.0, "confidence": 0.8}],
        },
    }

    window = SectionistMainWindow()
    try:
        window.display_results(payload)

        sections_text = window.sections_text.toPlainText()
        assert "Intro" in sections_text
        assert "Verse 1" in sections_text
        assert len(window.timeline.sections) == 2

        details_text = window.details_text.toPlainText()
        assert "120.0 BPM" in details_text
        assert "C major" in details_text
        assert "G major" in details_text
    finally:
        window.close()


def test_display_results_ignores_failed_payload(qapp):
    from main_window import SectionistMainWindow

    window = SectionistMainWindow()
    try:
        window.display_results({"success": False, "error": "backend exploded"})
        assert window.sections_text.toPlainText() == ""
        assert window.timeline.sections == []
    finally:
        window.close()


def test_modules_stay_reviewably_sized():
    # Guards against the entry point growing back into the old 1,200-line
    # monolith. Raise these deliberately if a module legitimately grows.
    limits = {
        "main_window.py": 900,
        "timeline_widget.py": 600,
        "audio_player.py": 200,
        "analysis_worker.py": 120,
    }

    oversized = {}
    for name, limit in limits.items():
        line_count = len((FRONTEND_DIR / name).read_text().splitlines())
        if line_count > limit:
            oversized[name] = (line_count, limit)

    assert oversized == {}, f"modules exceed their size budget: {oversized}"
