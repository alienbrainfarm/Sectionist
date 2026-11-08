"""Tests for the cycle region, automatic stems and the lyrics panel."""

import pytest
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QMouseEvent

DURATION = 40.0
WIDTH = 400  # 10 px per second


def test_snap_to_a_nearby_bar_line_only():
    from cycle import snap

    bars = [0.0, 4.0, 8.0]
    assert snap(3.4, bars, DURATION, WIDTH) == 4.0  # 6 px away: snaps
    assert snap(2.6, bars, DURATION, WIDTH) == 2.6  # 14 px away: stays
    assert snap(3.4, bars, DURATION, WIDTH, free=True) == 3.4
    assert snap(-1, [], DURATION, WIDTH) == 0.0


def test_hit_test_finds_edges_and_inside():
    from cycle import CycleRegion, hit_test

    region = CycleRegion(10.0, 20.0)
    assert hit_test(region, 102, DURATION, WIDTH) == "start"
    assert hit_test(region, 198, DURATION, WIDTH) == "end"
    assert hit_test(region, 150, DURATION, WIDTH) == "inside"
    assert hit_test(region, 300, DURATION, WIDTH) is None
    assert hit_test(None, 150, DURATION, WIDTH) is None


def test_drag_creates_resizes_and_moves_a_region():
    from cycle import CycleDrag, CycleRegion

    drag = CycleDrag()
    drag.press(None, 4.1, 41, DURATION, WIDTH)
    region = drag.move(11.9, [0.0, 4.0, 8.0, 12.0], DURATION, WIDTH)
    assert (region.start, region.end) == (4.0, 12.0)  # snapped to bars
    assert drag.release() is False  # a drag, not a click

    existing = CycleRegion(10.0, 20.0, enabled=False)
    drag.press(existing, 20.0, 200, DURATION, WIDTH)
    resized = drag.move(25.0, [], DURATION, WIDTH)
    assert (resized.start, resized.end, resized.enabled) == (10.0, 25.0, False)

    drag.press(existing, 15.0, 150, DURATION, WIDTH)
    moved = drag.move(39.0, [], DURATION, WIDTH)
    assert (moved.start, moved.end) == (30.0, 40.0)  # clamped to the song

    drag.press(existing, 15.0, 150, DURATION, WIDTH)
    assert drag.move(15.1, [], DURATION, WIDTH) is existing  # 1 px: a click
    assert drag.release() is True


def test_mixer_wraps_inside_the_region_without_a_gap():
    from test_stems import FakeStream, make_set

    from stem_player import StemPlayer

    player = StemPlayer(FakeStream)
    player.load_stems(make_set(seconds=1.0))
    player.set_loop((0.25, 0.5))  # frames 2000-4000
    player.set_position(0.45)  # 400 frames before the end
    block, finished = player.mix(1000)
    assert not finished and block[999, 0] != 0  # no silence at the seam
    assert player.frame == 2000 + 600

    # A playhead that starts after the region plays on, as in Logic.
    player.set_position(0.75)
    player.mix(100)
    assert player.frame == 6000 + 100
    player.set_loop(None)
    assert player.loop is None


def press(widget, x, y, kind=QMouseEvent.Type.MouseButtonPress, modifiers=None):
    event = QMouseEvent(
        kind,
        QPointF(x, y),
        QPointF(x, y),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        modifiers or Qt.KeyboardModifier.NoModifier,
    )
    {
        QMouseEvent.Type.MouseButtonPress: widget.mousePressEvent,
        QMouseEvent.Type.MouseMove: widget.mouseMoveEvent,
        QMouseEvent.Type.MouseButtonRelease: widget.mouseReleaseEvent,
    }[kind](event)


@pytest.fixture
def timeline(qapp):
    from timeline_widget import TimelineWidget

    widget = TimelineWidget()
    widget.resize(WIDTH, 180)
    widget.set_duration(DURATION)
    widget.set_downbeats([0.0, 4.0, 8.0, 12.0, 16.0])
    regions, seeks = [], []
    widget.cycle_changed.connect(regions.append)
    widget.section_clicked.connect(seeks.append)
    return widget, regions, seeks


def test_ruler_drag_makes_a_region_and_clicks_toggle_or_seek(timeline):
    widget, regions, seeks = timeline
    move, release = QMouseEvent.Type.MouseMove, QMouseEvent.Type.MouseButtonRelease

    press(widget, 41, 10)
    press(widget, 120, 10, move)
    press(widget, 120, 10, release)
    assert (regions[-1].start, regions[-1].end) == (4.0, 12.0)
    widget.cycle = regions[-1]

    press(widget, 80, 10)  # click on the region: cycle off
    press(widget, 80, 10, release)
    assert regions[-1].enabled is False

    press(widget, 300, 10)  # click elsewhere in the ruler: move the playhead
    press(widget, 300, 10, release)
    assert seeks == [30.0]
    widget.render(widget.grab())  # paints the region without error


@pytest.fixture
def window(qapp, monkeypatch):
    import stems_controller
    from main_window import SectionistMainWindow
    from test_stems import FakeStream

    monkeypatch.setattr(stems_controller, "playback_available", lambda: False)
    window = SectionistMainWindow()
    window.stems.stem_player._stream_factory = FakeStream
    window.timeline.set_duration(DURATION)
    window.timeline.set_sections(
        [
            {"name": "Verse", "start": 0.0, "end": 16.0},
            {"name": "Chorus", "start": 16.0, "end": 32.0},
        ]
    )
    yield window
    window.close()


def test_c_loops_the_current_section_then_toggles(window):
    cycle = window.cycle
    window.timeline.set_position(20.0)

    cycle.action.trigger()  # C with no region: loop the current section
    assert (cycle.region.start, cycle.region.end) == (16.0, 32.0)
    assert cycle.button.isChecked() and cycle.action.isChecked()
    assert window.stems.stem_player._loop_seconds == (16.0, 32.0)

    cycle.action.trigger()
    assert cycle.region.enabled is False and not cycle.button.isChecked()
    assert window.stems.stem_player._loop_seconds is None


def test_vlc_jumps_back_when_playback_crosses_the_end(window, monkeypatch):
    from cycle import CycleRegion

    seeks = []
    monkeypatch.setattr(window, "seek_to_position", seeks.append)
    window.cycle.set_region(CycleRegion(16.0, 32.0), snap=False)
    window.audio_player.is_playing = True

    window.cycle.on_position(31.9)
    assert seeks == []
    window.cycle.on_position(32.01)
    assert seeks == [16.0]

    window.cycle.on_position(16.05)
    window.cycle.on_position(35.0)  # the user clicked past the region
    window.cycle.on_position(35.05)  # and it plays on from there
    assert seeks == [16.0]


def test_new_song_clears_the_region(window):
    window.cycle.loop_current_section()
    window.clear_file()
    assert window.cycle.region is None and window.timeline.cycle is None


def test_stems_load_after_an_analysis_that_used_them(window, monkeypatch):
    import stems_controller

    requests = []
    monkeypatch.setattr(stems_controller, "playback_available", lambda: True)
    monkeypatch.setattr(
        window.stems,
        "split",
        lambda model, automatic=False: requests.append((model, automatic)),
    )
    window.current_file = "song.wav"

    window.stems.analysis_finished({"chord_source": "mix"})
    assert requests == []  # stems off on the backend: do not separate
    window.stems.analysis_finished({"chord_source": "stems"})
    assert requests == [("htdemucs", True)]


def test_lyrics_panel_opens_with_a_reason_when_there_are_none(window):
    window.display_results({"success": True, "analysis": {"sections": [{}]}})
    assert not window.lyrics_dock.isHidden()
    assert "faster-whisper" in window.lyrics_text.toPlainText()

    lines = [{"start": 0, "end": 2, "text": "hello there"}]
    analysis = {"sections": [{"start": 0, "end": 4}], "lyrics": lines}
    window.display_results({"success": True, "analysis": analysis})
    assert window.lyrics_text.toPlainText() == "[Section 1]\nhello there"

    window.display_results({"success": True, "analysis": {}})
    assert window.lyrics_text.toPlainText() == ""


def test_a_start_in_the_last_half_tick_still_loops(window, monkeypatch):
    from cycle import CycleRegion

    seeks = []
    monkeypatch.setattr(window, "seek_to_position", seeks.append)
    window.cycle.set_region(CycleRegion(16.0, 32.0), snap=False)
    window.audio_player.is_playing = True
    window.cycle.last_position = 31.99  # started 10 ms before the end
    window.cycle.on_position(32.04)
    assert seeks == [16.0]


def test_c_with_nothing_to_loop_leaves_cycle_off(qapp, monkeypatch):
    import stems_controller
    from main_window import SectionistMainWindow

    monkeypatch.setattr(stems_controller, "playback_available", lambda: False)
    window = SectionistMainWindow()
    try:
        window.cycle.action.trigger()  # no song, no sections
        window.cycle.button.click()
        assert window.cycle.region is None
        assert not window.cycle.action.isChecked()
        assert not window.cycle.button.isChecked()
    finally:
        window.close()


def test_cycle_region_is_saved_and_restored(window):
    from cycle import CycleRegion

    window.cycle.set_region(CycleRegion(4.0, 12.0, enabled=False))
    saved = window.cycle.saved()
    window.cycle.clear()
    window.cycle.restore(saved)
    region = window.cycle.region
    assert (region.start, region.end, region.enabled) == (4.0, 12.0, False)

    window.cycle.restore({"start": "nonsense"})
    assert window.cycle.region is None
    window.cycle.restore(None)
    assert window.cycle.region is None


def test_automatic_stems_can_be_switched_off(window, monkeypatch):
    import stems_controller

    requests = []
    monkeypatch.setattr(stems_controller, "playback_available", lambda: True)
    monkeypatch.setattr(
        window.stems, "split", lambda model, automatic=False: requests.append(model)
    )
    window.current_file = "song.wav"
    window.stems.auto_action.setChecked(False)
    try:
        window.stems.analysis_finished({"chord_source": "stems"})
        assert requests == []
    finally:
        window.stems.auto_action.setChecked(True)


def test_missing_lyrics_explain_which_case_it_is(window):
    from lyrics_view import NO_TRANSCRIBER, NO_VOCALS

    base = {"sections": [{"start": 0, "end": 4}]}
    window.display_results(
        {"success": True, "analysis": dict(base, lyrics_available=False)}
    )
    assert window.lyrics_text.toPlainText() == NO_TRANSCRIBER
    assert "machine running the backend" in NO_TRANSCRIBER
    window.display_results(
        {"success": True, "analysis": dict(base, lyrics_available=True)}
    )
    assert window.lyrics_text.toPlainText() == NO_VOCALS
