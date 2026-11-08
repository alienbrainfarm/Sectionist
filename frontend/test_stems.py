"""Tests for the stem splitter: mixing, waveforms, lanes, download and wiring.

No audio device or backend is needed: the output stream and HTTP calls are
replaced with fakes.
"""

import numpy as np
import pytest

RATE = 8000


class FakeStream:
    def __init__(self, samplerate, callback):
        self.samplerate = samplerate
        self.callback = callback
        self.stopped = True
        self.starts = 0
        self.closed = False

    def start(self):
        assert self.stopped, "PortAudio refuses to start a stream that is not stopped"
        self.stopped = False
        self.starts += 1

    def stop(self):
        self.stopped = True

    def close(self):
        self.closed = True


def make_set(seconds=1.0, names=("vocals", "drums", "bass", "other")):
    from stem_player import StemSet, compute_peaks

    frames = int(seconds * RATE)
    samples = {
        name: np.full((frames, 2), 1000 * (index + 1), dtype=np.int16)
        for index, name in enumerate(names)
    }
    stem_set = StemSet(RATE, samples, "htdemucs")
    stem_set.peaks = {name: compute_peaks(data) for name, data in samples.items()}
    return stem_set


@pytest.fixture
def player():
    from stem_player import StemPlayer

    streams = []

    def factory(rate, callback):
        streams.append(FakeStream(rate, callback))
        return streams[-1]

    player = StemPlayer(factory)
    player.load_stems(make_set(), "song.wav")
    player.streams = streams
    return player


def test_mix_sums_only_the_audible_stems(player):
    block, finished = player.mix(100)
    expected = (1000 + 2000 + 3000 + 4000) / 32768
    assert block[0, 0] == pytest.approx(expected)
    assert not finished

    player.set_audible(["drums"])
    block, _ = player.mix(100)
    assert block[0, 1] == pytest.approx(2000 / 32768)
    assert player.get_position() == pytest.approx(200 / RATE)


def test_mix_pads_the_last_block_and_reports_the_end(player):
    player.set_position(player.duration - 0.005)  # 40 frames left
    block, finished = player.mix(100)
    assert finished
    assert block[39, 0] != 0 and block[40:].any() == False  # noqa: E712


def test_seeks_are_exact_and_clamped(player):
    player.set_position(0.5)
    assert player.get_position() == 0.5
    player.set_position(99)
    assert player.get_position() == player.duration
    player.set_position(-3)
    assert player.get_position() == 0.0


def test_play_pause_stop_and_replay_after_the_end(player):
    player.play()
    assert player.is_playing and len(player.streams) == 1
    player.pause()
    assert player.is_paused and not player.is_playing
    player.play()
    assert player.streams[0].starts == 2

    # The song ran out: the callback stopped the stream from its own thread,
    # which leaves it inactive but not stopped.
    player.streams[0].stopped = False
    player.frame = make_set().frames
    player.is_playing = False
    player.play()
    assert player.get_position() == 0.0  # starts over
    assert player.streams[0].starts == 3

    player.stop()
    assert player.get_position() == 0.0 and not player.is_playing


def test_peaks_are_on_a_shared_scale():
    from stem_player import compute_peaks

    loud = compute_peaks(np.full((1000, 2), 32000, dtype=np.int16), bins=10)
    quiet = compute_peaks(np.full((1000, 2), 300, dtype=np.int16), bins=10)
    assert len(loud) == 10
    assert loud.max() > 0.95 and 0 < quiet.max() < 0.2
    assert len(compute_peaks(np.zeros((0, 2), dtype=np.int16))) == 0


def test_loading_pads_short_stems_and_widens_mono(tmp_path):
    import soundfile as sf

    from stem_player import load_stem_set

    sf.write(tmp_path / "vocals.flac", np.zeros((800, 2)), RATE)
    sf.write(tmp_path / "bass.flac", np.full(400, 0.5), RATE)  # mono, shorter
    stem_set = load_stem_set(
        {"vocals": tmp_path / "vocals.flac", "bass": tmp_path / "bass.flac"}
    )
    assert stem_set.samples["bass"].shape == (800, 2)
    assert (
        stem_set.samples["bass"][399, 1] > 0 and stem_set.samples["bass"][400, 0] == 0
    )
    assert set(stem_set.peaks) == {"vocals", "bass"}


def test_solo_wins_over_everything_else_and_mute_wins_over_solo():
    from stem_lanes import audible_stems

    names = ["vocals", "drums", "bass"]
    assert audible_stems(names, set(), set()) == names
    assert audible_stems(names, {"drums"}, set()) == ["vocals", "bass"]
    assert audible_stems(names, set(), {"bass"}) == ["bass"]
    assert audible_stems(names, {"bass"}, {"bass", "vocals"}) == ["vocals"]


def test_column_peaks_fit_any_width():
    from stem_lanes import column_peaks

    peaks = np.linspace(0, 1, 100, dtype=np.float32)
    assert len(column_peaks(peaks, 37)) == 37
    assert column_peaks(peaks, 1)[0] == pytest.approx(1.0)
    assert len(column_peaks(peaks, 400)) == 400
    assert len(column_peaks(np.zeros(0), 10)) == 10


def test_lanes_report_the_mix_and_paint(qapp):
    from PyQt6.QtGui import QPixmap

    from stem_lanes import StemLanes

    lanes = StemLanes()
    heard = []
    lanes.mix_changed.connect(heard.append)
    lanes.set_stems(make_set(), 1.0)
    lanes.set_sections([{"start": 0}, {"start": 0.5}])
    assert lanes.names() == ["vocals", "drums", "bass", "other"]

    lanes.toggle_mute("drums")
    assert heard[-1] == ["vocals", "bass", "other"]
    lanes.toggle_solo("bass")
    assert heard[-1] == ["bass"]
    assert lanes.rows[0].waveform.audible is False
    lanes.reset()
    assert heard[-1] == lanes.names()

    lanes.resize(700, 300)
    lanes.set_position(0.25)
    lanes.render(QPixmap(700, 300))
    lanes.show_message("Splitting stems… 40%")
    assert not lanes.has_stems and not lanes.isHidden()


# --- download -------------------------------------------------------------------


class FakeResponse:
    def __init__(self, status=200, body=None, content=b""):
        self.status_code = status
        self.body = body or {}
        self.content = content

    def json(self):
        return self.body

    def raise_for_status(self):
        assert self.status_code < 400

    def iter_content(self, _size):
        yield self.content

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


@pytest.fixture
def backend(monkeypatch, tmp_path):
    """A fake backend whose job finishes on the second poll."""
    import io

    import soundfile as sf

    import stems_client

    monkeypatch.setenv("SECTIONIST_STEMS_DIR", str(tmp_path / "stems"))
    monkeypatch.setattr(stems_client, "POLL_SECONDS", 0)
    buffer = io.BytesIO()
    sf.write(buffer, np.zeros((RATE, 2)), RATE, format="FLAC")
    calls = {"post": 0, "polls": 0, "downloads": []}

    def post(url, files, data, timeout):
        calls["post"] += 1
        assert url.endswith("/stems") and data == {"model": "htdemucs"}
        return FakeResponse(202, {"job_id": "j1", "status": "queued", "progress": 0})

    def get(url, timeout, stream=False):
        if stream:
            calls["downloads"].append(url.rsplit("/", 1)[1])
            return FakeResponse(content=buffer.getvalue())
        calls["polls"] += 1
        done = calls["polls"] > 1
        body = {"job_id": "j1", "status": "done" if done else "running"}
        body.update(progress=1.0 if done else 0.5, stems=["vocals", "other"])
        return FakeResponse(body=body)

    monkeypatch.setattr(stems_client.requests, "post", post)
    monkeypatch.setattr(stems_client.requests, "get", get)
    song = tmp_path / "song.wav"
    song.write_bytes(b"pretend audio")
    return song, calls


def test_worker_downloads_then_reuses_the_local_copy(qapp, backend):
    from stems_client import StemsWorker

    song, calls = backend
    worker = StemsWorker(str(song), "htdemucs")
    messages = []
    worker.progress.connect(lambda fraction, text: messages.append(text))

    stem_set = worker.fetch()
    assert stem_set.names == ["vocals", "other"]
    assert calls["downloads"] == ["vocals", "other"]
    assert "Splitting stems… 50%" in messages

    # Opening the song again looks in the cache only, and finds them.
    again = StemsWorker(str(song)).fetch()
    assert again.names == ["vocals", "other"] and again.model == "htdemucs"
    assert calls["post"] == 1


def test_worker_reports_backend_errors(qapp, backend, monkeypatch):
    import stems_client

    song, _calls = backend
    monkeypatch.setattr(
        stems_client.requests,
        "post",
        lambda *a, **k: FakeResponse(503, {"error": "Stem splitting needs Demucs"}),
    )
    with pytest.raises(RuntimeError, match="needs Demucs"):
        stems_client.StemsWorker(str(song), "htdemucs").fetch()
    assert stems_client.StemsWorker(str(song)).fetch() is None  # nothing cached


# --- main window ---------------------------------------------------------------


@pytest.fixture
def window(qapp, monkeypatch):
    import stems_controller
    from main_window import SectionistMainWindow

    monkeypatch.setattr(stems_controller, "playback_available", lambda: False)
    window = SectionistMainWindow()
    window.stems.stem_player._stream_factory = FakeStream
    yield window
    window.close()


def test_stems_take_over_playback_and_hand_it_back(window):
    original = window.audio_player
    window.timeline.set_duration(1.0)
    window.timeline.set_sections([{"name": "A", "start": 0, "end": 1}])

    window.stems.use_stems(make_set())
    assert window.audio_player is window.stems.stem_player
    assert not window.timeline_gutter.isHidden()
    assert window.stem_lanes.names() == ["vocals", "drums", "bass", "other"]

    window.seek_to_position(0.5)
    assert window.audio_player.get_position() == 0.5
    assert window.stem_lanes.rows[0].waveform.position == 0.5  # playhead follows

    window.stem_lanes.toggle_mute("vocals")
    assert "vocals" not in window.stems.stem_player.audible

    window.stems.use_original()
    assert window.audio_player is original
    assert not window.stem_lanes.has_stems
    assert window.timeline_gutter.isHidden()


def test_split_button_and_menu_follow_the_song(window):
    assert window.stems.button.isEnabled() is False
    labels = [a.text() for a in window.analysis_menu.actions()]
    assert "Split &Stems" in labels

    window.stems.song_changed("song.wav")
    assert window.stems.button.isEnabled()
    window.stems.song_changed(None)
    assert window.stems.button.isEnabled() is False


def test_slash_chords_take_their_root_colour(qapp):
    from chord_track import chord_color

    assert chord_color("C/E") == chord_color("C")
    assert chord_color("Am/C") == chord_color("Am")


def test_details_say_when_chords_came_from_stems():
    from results_text import format_details

    analysis = {"chords": [{"name": "C/E", "start": 0, "end": 2}]}
    assert "FROM STEMS" not in format_details(analysis)
    analysis["chord_source"] = "stems"
    assert "FROM STEMS" in format_details(analysis)  # headings are upper case


def test_stem_waveforms_line_up_with_the_timeline(window, qapp):
    from PyQt6.QtCore import QPoint

    window.resize(1400, 900)
    window.pages.setCurrentWidget(window.workspace)
    window.show()
    window.timeline.set_duration(1.0)
    window.stems.use_stems(make_set())
    qapp.processEvents()

    timeline = window.timeline
    waveform = window.stem_lanes.rows[0].waveform
    # Same left edge and width, so a moment in time is the same x in both.
    assert (
        timeline.mapTo(window, QPoint(0, 0)).x()
        == waveform.mapTo(window, QPoint(0, 0)).x()
    )
    assert timeline.width() == waveform.width()


def test_window_starts_without_numpy_installed():
    import os
    import subprocess
    import sys
    from pathlib import Path

    # numpy is only needed for stems; an existing install must still start.
    script = (
        "import sys; sys.modules['numpy'] = None\n"
        "from PyQt6.QtWidgets import QApplication\n"
        "app = QApplication([])\n"
        "import stem_player\n"
        "from main_window import SectionistMainWindow\n"
        "window = SectionistMainWindow()\n"
        "assert stem_player.playback_available() is False\n"
        "print('started')\n"
    )
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert "started" in result.stdout, result.stderr


def test_local_cache_is_capped_and_can_be_cleared(monkeypatch, tmp_path):
    import os

    import stems_client

    monkeypatch.setenv("SECTIONIST_STEMS_DIR", str(tmp_path))
    folders = []
    for index in range(3):
        folder = tmp_path / f"key{index}-htdemucs"
        folder.mkdir()
        (folder / "vocals.flac").write_bytes(b"x" * 1024 * 1024)
        os.utime(folder, (1000 + index, 1000 + index))
        folders.append(folder)

    removed = stems_client.prune_cache(limit_mb=2.5, keep=folders[0])
    assert removed == [folders[1]]  # oldest that is not being kept
    assert stems_client.clear_cache() == pytest.approx(2.0)
    assert not tmp_path.exists()


def test_clear_cache_is_in_the_analysis_menu(window, monkeypatch):
    import stems_controller

    monkeypatch.setattr(stems_controller, "clear_cache", lambda: 12.0)
    assert window.stems.clear_action in window.analysis_menu.actions()
    window.stems.clear_action.trigger()
    assert "12 MB" in window.status_label.text()
