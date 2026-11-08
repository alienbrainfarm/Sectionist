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
        assert window.sections_table is not None
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
            "downbeats": [0.0, 20.0, 40.0],
            "chords": [{"name": "C", "start": 0.0, "end": 4.0, "confidence": 0.8}],
        },
    }

    window = SectionistMainWindow()
    try:
        window.display_results(payload)

        sections_text = window.sections_table.toPlainText()
        assert "Intro" in sections_text
        assert "Verse 1" in sections_text
        assert len(window.timeline.sections) == 2
        assert len(window.timeline.chords) == 1
        assert window.timeline.downbeats == [0.0, 20.0, 40.0]

        details_text = window.details_text.toPlainText()
        assert "120.0 BPM" in details_text
        assert "C major" in details_text
        assert "G major" in details_text
    finally:
        window.close()


def test_sections_without_confidence_show_a_dash(qapp):
    """Model-based engines omit confidence; the panel must not crash on it."""
    from main_window import SectionistMainWindow

    payload = {
        "success": True,
        "analysis": {
            "duration": 30.0,
            "tempo": 100.0,
            "key": "A minor",
            "key_changes": [],
            "sections": [{"name": "Verse 1", "start": 0.0, "end": 30.0}],
            "beats_detected": 50,
            "chords": [],
            "engine": "songformer",
        },
    }

    window = SectionistMainWindow()
    try:
        window.display_results(payload)

        table = window.sections_table
        assert table.cell_text(0, 0) == "Verse 1"
        assert table.cell_text(0, 5) == "—"
        assert "songformer" in window.details_text.toPlainText()
    finally:
        window.close()


def test_display_results_ignores_failed_payload(qapp):
    from main_window import SectionistMainWindow

    window = SectionistMainWindow()
    try:
        window.display_results({"success": False, "error": "backend exploded"})
        assert window.sections_table.rowCount() == 0
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
        "panels.py": 400,
        "theme.py": 400,
        "timeline_paint.py": 300,
        "stem_lanes.py": 400,
        "stem_player.py": 250,
        "stems_client.py": 220,
        "stems_controller.py": 220,
    }

    oversized = {}
    for name, limit in limits.items():
        source = (FRONTEND_DIR / name).read_text(encoding="utf-8")
        line_count = len(source.splitlines())
        if line_count > limit:
            oversized[name] = (line_count, limit)

    assert oversized == {}, f"modules exceed their size budget: {oversized}"


def test_chord_track_renders_without_error(qapp):
    """Painting with a chord track must not raise (it is pure paint code)."""
    from PyQt6.QtGui import QPixmap

    from timeline_widget import TimelineWidget

    widget = TimelineWidget()
    widget.resize(800, 160)
    widget.set_duration(60.0)
    widget.set_sections([{"name": "Verse", "start": 0.0, "end": 60.0}])
    widget.set_chords(
        [
            {"name": "D", "start": 0.0, "end": 20.0},
            {"name": "Em", "start": 20.0, "end": 40.0},
            {"name": "A", "start": 40.0, "end": 60.0},
        ]
    )

    pixmap = QPixmap(800, 160)
    widget.render(pixmap)

    assert len(widget.chords) == 3
    assert not pixmap.isNull()


def test_chord_colours_distinguish_quality():
    from chord_track import chord_color

    assert chord_color("C").name() != chord_color("Cm").name()
    assert chord_color("Am").name() != chord_color("A").name()
    # Unknown labels fall back to grey rather than raising.
    assert chord_color("??").name() == "#8a8a8a"


def test_chord_geometry_hit_testing():
    from chord_track import chord_at_position, chord_boundary_at

    chords = [
        {"name": "D", "start": 0.0, "end": 20.0},
        {"name": "Em", "start": 20.0, "end": 40.0},
    ]

    # 800 px over 40 s -> 20 px per second
    assert chord_at_position(chords, 40, 800, 100) == 0
    assert chord_at_position(chords, 40, 800, 500) == 1
    assert chord_boundary_at(chords, 40, 800, 400) == 0
    assert chord_boundary_at(chords, 40, 800, 300) == -1


def test_renaming_a_chord_updates_results(qapp):
    from main_window import SectionistMainWindow

    payload = {
        "success": True,
        "analysis": {
            "duration": 40.0,
            "tempo": 100.0,
            "key": "D major",
            "key_changes": [],
            "sections": [{"name": "Verse", "start": 0.0, "end": 40.0}],
            "beats_detected": 50,
            "chords": [
                {"name": "D", "start": 0.0, "end": 20.0},
                {"name": "Em", "start": 20.0, "end": 40.0},
            ],
        },
    }

    window = SectionistMainWindow()
    try:
        window.analysis_results = payload
        window.display_results(payload)

        window.rename_chord(0, "Dm")

        assert payload["analysis"]["chords"][0]["name"] == "Dm"
        assert window.timeline.chords[0]["name"] == "Dm"
        assert "Dm" in window.details_text.toPlainText()
    finally:
        window.close()


def test_dragging_a_chord_boundary_keeps_chords_contiguous(qapp):
    from main_window import SectionistMainWindow

    payload = {
        "success": True,
        "analysis": {
            "duration": 40.0,
            "tempo": 100.0,
            "key": "D major",
            "key_changes": [],
            "sections": [],
            "beats_detected": 50,
            "chords": [
                {"name": "D", "start": 0.0, "end": 20.0},
                {"name": "Em", "start": 20.0, "end": 40.0},
            ],
        },
    }

    window = SectionistMainWindow()
    try:
        window.analysis_results = payload
        window.display_results(payload)

        window.move_chord_boundary(0, 26.5)

        chords = payload["analysis"]["chords"]
        assert chords[0]["end"] == 26.5
        assert chords[1]["start"] == 26.5

        # A drag past the neighbour is clamped, never inverted.
        window.move_chord_boundary(0, 999.0)
        assert chords[0]["end"] < chords[1]["end"]
        assert chords[0]["end"] == chords[1]["start"]
    finally:
        window.close()


def test_bar_lines_render(qapp):
    from PyQt6.QtGui import QPixmap

    from timeline_widget import TimelineWidget

    widget = TimelineWidget()
    widget.resize(800, 160)
    widget.set_duration(60.0)
    widget.set_sections([{"name": "Verse", "start": 0.0, "end": 60.0}])
    widget.set_downbeats([index * 2.0 for index in range(1, 30)])

    pixmap = QPixmap(800, 160)
    widget.render(pixmap)

    assert len(widget.downbeats) == 29
    assert not pixmap.isNull()


def test_format_lyrics_groups_stanzas_on_pauses():
    from lyrics_view import format_lyrics

    lines = [
        {"start": 0.0, "end": 4.0, "text": "first line"},
        {"start": 4.0, "end": 8.0, "text": "second line"},
        {"start": 14.0, "end": 18.0, "text": "after a gap"},
        {"start": 18.0, "end": 22.0, "text": "same stanza"},
    ]

    assert format_lyrics(lines) == "first line\nsecond line\n\nafter a gap\nsame stanza"


def test_lyrics_panel_populates_from_results(qapp):
    from main_window import SectionistMainWindow

    payload = {
        "success": True,
        "analysis": {
            "duration": 30.0,
            "tempo": 100.0,
            "key": "D major",
            "key_changes": [],
            "sections": [{"name": "Verse", "start": 0.0, "end": 30.0}],
            "beats_detected": 40,
            "chords": [],
            "lyrics": [
                {"start": 0.0, "end": 4.0, "text": "be on my side"},
                {"start": 4.0, "end": 8.0, "text": "there is no reason"},
            ],
        },
    }

    window = SectionistMainWindow()
    try:
        window.display_results(payload)

        text = window.lyrics_text.toPlainText()
        assert "be on my side" in text
        assert "there is no reason" in text
        assert not window.lyrics_dock.isHidden()
    finally:
        window.close()


def test_format_lyrics_breaks_on_section_change():
    from lyrics_view import format_lyrics

    lines = [
        {"start": 0.0, "end": 4.0, "text": "a"},
        {"start": 4.0, "end": 8.0, "text": "b"},
        {"start": 8.0, "end": 12.0, "text": "c"},
        {"start": 12.0, "end": 16.0, "text": "d"},
    ]
    sections = [{"start": 0.0, "end": 8.0}, {"start": 8.0, "end": 16.0}]

    assert format_lyrics(lines, sections) == "a\nb\n\nc\nd"


def test_format_lyrics_never_leaves_a_one_line_stanza():
    from lyrics_view import format_lyrics

    lines = [
        {"start": 0.0, "end": 4.0, "text": "a"},
        {"start": 4.0, "end": 8.0, "text": "b"},
    ]
    # The section changes after a single line, which should not split it off.
    sections = [{"start": 0.0, "end": 4.0}, {"start": 4.0, "end": 8.0}]

    assert format_lyrics(lines, sections) == "a\nb"


def test_shutdown_is_safe_with_nothing_playing(qapp):
    """Ctrl-C calls this; it must not raise when nothing is loaded."""
    from main_window import SectionistMainWindow

    window = SectionistMainWindow()
    try:
        window.shutdown()  # no playback, no worker
        window.shutdown()  # idempotent
    finally:
        window.close()
