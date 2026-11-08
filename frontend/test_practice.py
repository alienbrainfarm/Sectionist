"""Tests for practice features: loop snap, locks, lyrics editing, mix export
and the gig sheet."""

import numpy as np
import pytest

SECTIONS = [
    {"name": "Verse", "start": 0.0, "end": 8.0},
    {"name": "Chorus", "start": 8.0, "end": 16.0},
]
CHORDS = [
    {"name": "D", "start": 0.0, "end": 2.0},
    {"name": "A", "start": 2.0, "end": 3.0},
    {"name": "Bm", "start": 3.0, "end": 4.0},
    {"name": "G", "start": 4.0, "end": 8.0},
    {"name": "G", "start": 8.0, "end": 16.0},
]
DOWNBEATS = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0]
LYRICS = [
    {"start": 0.5, "end": 2.0, "text": "first verse line"},
    {"start": 9.0, "end": 11.0, "text": "chorus line"},
]


@pytest.fixture
def window(qapp, monkeypatch):
    import stems_controller
    from main_window import SectionistMainWindow
    from test_stems import FakeStream

    monkeypatch.setattr(stems_controller, "playback_available", lambda: False)
    window = SectionistMainWindow()
    window.stems.stem_player._stream_factory = FakeStream
    window.current_file = "C:/music/My Song.mp3"
    analysis = {
        "sections": [dict(s) for s in SECTIONS],
        "chords": [dict(c) for c in CHORDS],
        "downbeats": DOWNBEATS,
        "lyrics": LYRICS,
        "key": "D major",
        "tempo": 120.0,
        "duration": 16.0,
    }
    window.analysis_results = {"success": True, "analysis": analysis}
    window.timeline.set_duration(16.0)
    window.display_results(window.analysis_results)
    yield window
    window.close()


# --- loop snap -----------------------------------------------------------------


def test_turning_a_loop_on_moves_the_playhead_to_its_start(window, monkeypatch):
    from cycle import CycleRegion

    seeks = []
    monkeypatch.setattr(window, "seek_to_position", seeks.append)
    window.timeline.set_position(12.0)

    window.cycle.set_region(CycleRegion(4.0, 8.0))
    assert seeks == [4.0]  # a new loop starts at its top
    window.cycle.toggle()  # off: stay put
    window.cycle.toggle()  # on again: back to the top
    assert seeks == [4.0, 4.0]

    window.timeline.current_position = 5.0
    window.cycle.set_region(CycleRegion(4.0, 9.0))  # widened, playhead inside
    assert seeks == [4.0, 4.0]
    window.cycle.set_region(CycleRegion(6.0, 9.0))  # moved past the playhead
    assert seeks == [4.0, 4.0, 6.0]

    window.cycle.clear()
    window.cycle.restore({"start": 1.0, "end": 2.0, "enabled": True})
    assert seeks == [4.0, 4.0, 6.0]  # restoring a saved song does not jump


# --- locks ---------------------------------------------------------------------


def test_locked_sections_and_chords_take_no_edits(window, monkeypatch):
    import timeline_widget

    asked = []
    monkeypatch.setattr(
        timeline_widget.QInputDialog,
        "getText",
        lambda *a, **k: asked.append(a) or ("New", True),
    )
    timeline = window.timeline
    split = []
    timeline.section_split.connect(lambda *a: split.append(a))

    window.timeline_gutter.sections_lock.click()
    assert window.locks.actions["sections"].isChecked()
    edge_x = 8.0 / 16.0 * timeline.width()
    assert timeline.get_resize_mode(edge_x, 0) is None
    timeline.start_rename_section(0)
    timeline.split_section_at_position(0, 10)
    assert asked == [] and split == []

    window.locks.actions["chords"].trigger()
    assert timeline.get_chord_boundary(2.0 / 16.0 * timeline.width()) == -1
    timeline.start_rename_chord(0)
    assert asked == []

    window.locks.set_locked("sections", False)
    timeline.start_rename_section(0)
    assert len(asked) == 1  # unlocked again: editing works


def test_locked_lyrics_are_read_only_and_edits_are_kept(window):
    text = window.lyrics_text
    assert not text.isReadOnly()
    text.moveCursor(text.textCursor().MoveOperation.End)
    text.insertPlainText("\nmy own line")
    stored = window.analysis_results["analysis"]["lyrics_text"]
    assert stored.endswith("my own line")

    window.locks.buttons["lyrics"].click()
    assert text.isReadOnly() and window.locks.actions["lyrics"].isChecked()


def test_reanalysis_keeps_what_is_locked(window):
    window.locks.set_locked("sections", True)
    window.locks.set_locked("lyrics", True)
    window.analysis_results["analysis"]["lyrics_text"] = "[Verse]\nedited"
    fresh = {
        "success": True,
        "analysis": {
            "sections": [{"name": "Intro", "start": 0.0, "end": 16.0}],
            "chords": [{"name": "E", "start": 0.0, "end": 16.0}],
            "lyrics": [{"start": 1.0, "end": 2.0, "text": "new"}],
        },
    }
    window.analysis_finished(fresh)
    analysis = window.analysis_results["analysis"]
    assert [s["name"] for s in analysis["sections"]] == ["Verse", "Chorus"]
    assert analysis["chords"][0]["name"] == "E"  # chords were not locked
    assert analysis["lyrics_text"] == "[Verse]\nedited"
    assert window.lyrics_text.toPlainText() == "[Verse]\nedited"


def test_locks_are_saved_restored_and_reset(window):
    window.locks.set_locked("chords", True)
    assert window.addons.saved()["locks"] == {
        "sections": False,
        "chords": True,
        "lyrics": False,
    }
    window.addons.song_changed("other.mp3")
    assert not any(window.locks.locked.values())
    window.addons.song_loaded({"locks": {"lyrics": True}})
    assert window.locks.locked["lyrics"] and window.lyrics_text.isReadOnly()


# --- lyrics by section -----------------------------------------------------------


def test_lyrics_are_grouped_under_section_headers():
    from lyrics_view import lyrics_by_section, lyrics_per_section

    text = lyrics_by_section(LYRICS, SECTIONS)
    assert text == "[Verse]\nfirst verse line\n\n[Chorus]\nchorus line"
    # Every section keeps a header, sung or not.
    instrumental = lyrics_by_section(LYRICS[:1], SECTIONS)
    assert instrumental.endswith("[Chorus]")
    assert lyrics_per_section({"lyrics": LYRICS}, SECTIONS) == [
        "first verse line",
        "chorus line",
    ]


def test_edited_lyrics_map_back_to_sections_by_order():
    from lyrics_view import lyrics_per_section

    edited = "a note first\n[Verse 1 renamed]\nline one\nline two\n[Chorus]\nhey"
    per = lyrics_per_section({"lyrics_text": edited}, SECTIONS)
    assert per == ["a note first\nline one\nline two", "hey"]
    assert lyrics_per_section({"lyrics_text": "no headers"}, SECTIONS) == [
        "no headers",
        "",
    ]


# --- mix export -----------------------------------------------------------------


def test_render_mix_sums_the_chosen_stems_over_the_range():
    from mix_export import render_mix
    from test_stems import RATE, make_set

    stem_set = make_set(seconds=1.0)  # vocals 1000, drums 2000, bass 3000, other 4000
    mix = render_mix(stem_set, ["drums", "bass"], 0.25, 0.5)
    assert len(mix) == RATE // 4
    assert mix[len(mix) // 2, 0] == pytest.approx(5000 / 32768)
    assert mix[0, 0] == 0.0  # faded in, no click at the cut

    loud = render_mix(stem_set, stem_set.names)  # 10000 * 4 would clip
    assert np.abs(loud).max() <= 0.98 + 1e-6


def test_mixes_write_as_mp3_and_wav(tmp_path):
    import soundfile as sf

    from mix_export import write_mix

    t = np.arange(44100) / 44100
    tone = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    samples = np.stack([tone, tone], axis=1)
    write_mix(samples, 44100, tmp_path / "mix.wav")
    data, rate = sf.read(tmp_path / "mix.wav")
    assert rate == 44100 and data.shape == (44100, 2)

    write_mix(samples, 44100, tmp_path / "mix.mp3")
    head = (tmp_path / "mix.mp3").read_bytes()[:3]
    assert head == b"ID3" or head[0] == 0xFF  # an MP3 stream
    assert (tmp_path / "mix.mp3").stat().st_size > 10000


def test_export_names_say_what_is_in_the_mix():
    from cycle import CycleRegion
    from mix_export import default_name

    names = ["vocals", "drums", "bass", "other"]
    assert default_name("x/Song.mp3", names, names, None) == "Song - mix.mp3"
    assert (
        default_name("Song.mp3", ["drums", "bass", "other"], names, None)
        == "Song - no vocals.mp3"
    )
    assert (
        default_name("Song.mp3", ["bass"], names, CycleRegion(48, 61.8))
        == "Song - bass (0:48-1:01).mp3"
    )


def test_export_without_stems_explains_itself(window, monkeypatch):
    import mix_export

    told = []
    monkeypatch.setattr(
        mix_export.QMessageBox, "information", lambda *a: told.append(a[2])
    )
    window.mix_export.export()
    assert "stems" in told[0]
    assert window.mix_export.action.shortcut().toString() == "Ctrl+E"


def test_export_writes_the_loop_of_audible_stems(window, monkeypatch, tmp_path):
    import soundfile as sf

    import mix_export
    from cycle import CycleRegion
    from test_stems import RATE, make_set

    window.stems.use_stems(make_set(seconds=1.0))
    window.stem_lanes.toggle_mute("vocals")
    window.cycle.set_region(CycleRegion(0.5, 0.75))
    target = tmp_path / "loop.wav"
    monkeypatch.setattr(
        mix_export.QFileDialog,
        "getSaveFileName",
        lambda *a: (str(target), "WAV audio (*.wav)"),
    )
    window.mix_export.export()
    window.mix_export.worker.wait(10000)
    data, rate = sf.read(target)
    assert rate == RATE and len(data) == RATE // 4


# --- gig sheet ------------------------------------------------------------------


def test_bar_chords_follow_the_downbeats():
    from gig_sheet import bar_chords, chord_grid

    bars = bar_chords(CHORDS, DOWNBEATS, 0.0, 8.0)
    assert bars == [["D"], ["A", "Bm"], ["G"], ["G"]]
    assert chord_grid(bars) == ["| D     | A  Bm | G     | %     |"]
    assert bar_chords([], [0.0, 2.0], 0.0, 4.0) == [["N.C."], ["N.C."]]


def test_sheet_has_every_section_with_chords_and_lyrics(window):
    from gig_sheet import sheet_html

    window.analysis_results["analysis"][
        "lyrics_text"
    ] = "[Verse]\nfirst <verse> line\n\n[Chorus]\nchorus line"
    html = sheet_html("My Song", window.analysis_results["analysis"])
    assert "My Song" in html and "D major" in html and "120 BPM" in html
    assert html.index("Verse") < html.index("Chorus")
    assert "first &lt;verse&gt; line" in html  # escaped
    assert "A&nbsp;&nbsp;Bm" in html


def test_gig_sheet_exports_a_pdf(window, tmp_path):
    path = window.gig_sheet.export_pdf(str(tmp_path / "sheet.pdf"))
    data = (tmp_path / "sheet.pdf").read_bytes()
    assert path and data.startswith(b"%PDF") and len(data) > 1000
    assert window.gig_sheet.print_action.shortcut().toString() == "Ctrl+P"
