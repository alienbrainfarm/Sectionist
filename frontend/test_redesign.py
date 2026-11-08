"""Tests for the redesigned window: theme, panels and page switching."""

PAYLOAD = {
    "success": True,
    "analysis": {
        "duration": 40.0,
        "tempo": 96.0,
        "key": "E minor",
        "key_changes": [],
        "sections": [
            {"name": "Intro", "start": 0.0, "end": 10.0},
            {"name": "Chorus", "start": 10.0, "end": 40.0, "confidence": 0.5},
        ],
        "beats_detected": 64,
        "downbeats": [0.0, 2.5, 5.0, 7.5, 10.0, 20.0, 30.0],
        "chords": [
            {"name": "Em", "start": 0.0, "end": 5.0},
            {"name": "Em", "start": 5.0, "end": 10.0},
            {"name": "C", "start": 10.0, "end": 20.0},
            {"name": "G", "start": 20.0, "end": 40.0},
        ],
        "engine": "songformer",
    },
}


def test_section_colours_match_by_type():
    from theme import DEFAULT_SECTION_COLOR, SECTION_COLORS, section_color

    assert section_color("Verse 2") == SECTION_COLORS["verse"]
    # Pre-chorus must not be painted as a chorus, however it is spelled.
    for name in ("Pre-Chorus", "pre chorus", "Prechorus"):
        assert section_color(name) == SECTION_COLORS["pre-chorus"], name
    assert section_color("Chorus") == SECTION_COLORS["chorus"]
    assert section_color("Mystery") == DEFAULT_SECTION_COLOR


def test_label_colour_contrasts_with_fill():
    from theme import text_color_on

    assert text_color_on("#FFFFFF").lightness() < 50
    assert text_color_on("#000000").lightness() > 200


def test_section_chords_collapse_repeats():
    from panels import bar_count, section_chords

    chords = PAYLOAD["analysis"]["chords"]
    assert section_chords(chords, 0.0, 10.0) == ["Em"]
    assert section_chords(chords, 10.0, 40.0) == ["C", "G"]
    assert bar_count(PAYLOAD["analysis"]["downbeats"], 0.0, 10.0) == 4


def test_section_chords_include_a_chord_carried_over():
    from panels import section_chords

    chords = [
        {"name": "Am", "start": 0.0, "end": 30.0},
        {"name": "F", "start": 30.0, "end": 31.0},
    ]
    # Am began before the section but is what you hear inside it.
    assert section_chords(chords, 20.0, 30.0) == ["Am"]
    # A chord that only grazes the boundary does not count.
    assert section_chords(chords, 29.9, 40.0) == ["F"]


def test_seek_while_stopped_is_applied_when_playback_starts():
    import vlc

    from audio_player import AudioPlayer

    class FakeVLC:
        def __init__(self):
            self.positions = []

        def play(self):
            pass

        def get_state(self):
            return vlc.State.Playing

        def set_position(self, ratio):
            self.positions.append(ratio)

        def get_position(self):
            return 0.0

    player = AudioPlayer()
    fake = FakeVLC()
    player._media_player = fake
    player.current_file = "song.wav"
    player.duration = 100.0

    player.set_position(40.0)
    assert fake.positions == []  # VLC would ignore it while stopped
    assert player.get_position() == 40.0  # the UI still shows where it will start

    player.play()
    assert fake.positions == [0.4]
    assert player.pending_seek is None


def test_chord_vocabulary_orders_by_time_used():
    from results_text import chord_vocabulary

    vocabulary = chord_vocabulary(PAYLOAD["analysis"]["chords"])
    assert vocabulary == [("G", 20.0), ("C", 10.0), ("Em", 10.0)]


def test_sections_table_shows_bars_chords_and_confidence(qapp):
    from main_window import SectionistMainWindow

    window = SectionistMainWindow()
    try:
        window.display_results(PAYLOAD)
        table = window.sections_table
        assert table.rowCount() == 2
        assert table.cell_text(0, 3) == "4"
        assert table.cell_text(1, 4) == "C  G"
        assert table.cell_text(1, 5) == "50%"
        assert "E minor" in window.details_text.toPlainText()
    finally:
        window.close()


def test_window_starts_on_the_drop_page_and_closes_back_to_it(qapp):
    from main_window import SectionistMainWindow

    window = SectionistMainWindow()
    try:
        assert window.pages.currentWidget() is window.empty_state
        window.pages.setCurrentWidget(window.workspace)
        window.display_results(PAYLOAD)

        window.clear_file()

        assert window.pages.currentWidget() is window.empty_state
        assert window.sections_table.rowCount() == 0
        assert window.timeline.sections == []
        assert window.play_button.isEnabled() is False
    finally:
        window.close()


def test_current_section_follows_the_playhead(qapp):
    from main_window import SectionistMainWindow

    window = SectionistMainWindow()
    try:
        window.display_results(PAYLOAD)
        window.timeline.set_duration(40.0)
        window.timeline.set_position(15.0)
        window.update_current_section()

        assert window.timeline.current_section() == 1
        assert window.transport.section_label.text() == "Chorus"
    finally:
        window.close()


def test_timeline_paints_placeholder_and_hover(qapp):
    from PyQt6.QtGui import QPixmap

    from timeline_widget import TimelineWidget

    widget = TimelineWidget()
    widget.resize(600, 180)
    widget.set_duration(40.0)
    widget.placeholder_text = "Analyzing…"
    pixmap = QPixmap(600, 180)
    widget.render(pixmap)  # no sections yet: placeholder path

    widget.set_sections(PAYLOAD["analysis"]["sections"])
    widget.hover_section = 1
    widget.drag_time_display = "0:12.000"
    widget.render(pixmap)
    assert not pixmap.isNull()


def test_slow_vlc_start_does_not_freeze_and_seek_lands_on_a_tick():
    import time

    import vlc

    from audio_player import AudioPlayer

    class SlowVLC:
        def __init__(self):
            self.state = vlc.State.Opening
            self.positions = []

        def play(self):
            pass

        def get_state(self):
            return self.state

        def set_position(self, ratio):
            self.positions.append(ratio)

        def get_position(self):
            return 0.0

    player = AudioPlayer()
    fake = SlowVLC()
    player._media_player = fake
    player.current_file = "song.wav"
    player.duration = 100.0
    player.set_position(25.0)

    started = time.monotonic()
    player.play()
    assert time.monotonic() - started < 0.5  # the old wait was a full second
    assert fake.positions == []  # VLC is not ready: keep the seek

    player.set_position(50.0)  # a click while VLC is still opening
    player.apply_pending_seek()
    assert fake.positions == []

    fake.state = vlc.State.Playing
    player.apply_pending_seek()  # the next playback tick
    assert fake.positions == [0.5]
    assert player.pending_seek is None


def test_bar_count_snaps_to_the_nearest_downbeat():
    from panels import bar_count

    downbeats = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0]
    assert bar_count(downbeats, 0.0, 8.0) == 4
    # Detected boundaries a little after the downbeat still count the bar.
    assert bar_count(downbeats, 2.1, 8.1) == 3
    assert bar_count(downbeats, 1.9, 7.9) == 3
    assert bar_count([], 0.0, 8.0) == 0


def test_chord_totals_read_as_durations():
    from results_text import _held_for, format_details

    assert _held_for(72) == "1m 12s"
    assert _held_for(9.6) == "10s"
    html = format_details(PAYLOAD["analysis"])
    assert "20s" in html and "0:20" not in html


def test_file_names_are_shown_as_plain_text(qapp):
    from PyQt6.QtCore import Qt

    from panels import HeaderBar, TransportBar

    header = HeaderBar()
    header.set_song("<b>Rock & Roll</b>.mp3", "")
    assert header.title_label.textFormat() == Qt.TextFormat.PlainText
    assert header.meta_label.textFormat() == Qt.TextFormat.PlainText
    assert TransportBar().section_label.textFormat() == Qt.TextFormat.PlainText


def test_chord_edits_without_results_do_not_crash(qapp):
    from main_window import SectionistMainWindow

    window = SectionistMainWindow()
    try:
        assert window.analysis_results is None
        assert window.chord_list() == []
        window.rename_chord(0, "Am")
    finally:
        window.close()
