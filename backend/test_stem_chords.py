"""Tests for chord recognition from stems, anchored on the bass."""

import io
from unittest.mock import patch

import numpy as np
import pytest

SR = 22050
BEAT = 0.5
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def tones(midis, seconds, harmonics=1):
    t = np.arange(int(SR * seconds)) / SR
    signal = sum(
        np.sin(2 * np.pi * hz(m) * k * t) / k
        for m in midis
        for k in range(1, harmonics + 1)
    )
    return signal * np.minimum(1, t * 50)


def bars(notes_per_bar, octave, beats_per_bar=4, harmonics=1):
    """One block per bar: a list of note names played for the whole bar."""
    blocks = []
    for names in notes_per_bar:
        midis = [12 * (octave + 1) + NOTE[name] for name in names]
        blocks.append(tones(midis, beats_per_bar * BEAT, harmonics))
    return np.concatenate(blocks)


def grid(count_bars, beats_per_bar=4):
    beats = [i * BEAT for i in range(count_bars * beats_per_bar)]
    return beats, beats[::beats_per_bar]


def detect(harmony, bass, **kwargs):
    from analysis.stem_chords import detect_chords_from_stems

    beats, downbeats = grid(len(harmony) // int(4 * BEAT * SR))
    return detect_chords_from_stems(harmony, bass, SR, beats, downbeats, **kwargs)


def names(chords):
    return [chord["name"] for chord in chords]


def test_bass_decides_between_relative_chords():
    # C and E are in both C major and A minor; only the bass tells them apart.
    harmony = bars([["C", "E"]] * 4, octave=4)
    as_a_minor = bars([["A"], ["A"], ["C"], ["C"]], octave=2, harmonics=4)
    chords = detect(harmony, as_a_minor)
    assert names(chords) == ["Am", "C"]
    assert chords[1]["start"] == pytest.approx(4.0, abs=0.3)


def test_bass_on_the_third_is_named_as_an_inversion():
    harmony = bars([["C", "E", "G"]] * 4, octave=4)
    bass = bars([["E"]] * 4, octave=2, harmonics=4)
    assert names(detect(harmony, bass)) == ["C/E"]
    assert names(detect(harmony, bass, slash=False)) == ["C"]


def test_harmony_alone_still_works_without_a_bass():
    harmony = bars([["G", "B", "D"]] * 2 + [["D", "F", "A"]] * 2, octave=4)
    silent = np.zeros_like(harmony)
    assert names(detect(harmony, silent)) == ["G", "Dm"]
    assert names(detect(harmony, None)) == ["G", "Dm"]


def test_bass_fundamental_beats_its_own_overtones():
    from analysis.stem_chords import bass_per_beat, bass_salience

    # A strong third harmonic puts energy on E; the note is still A.
    bass = tones([45], 2.0, harmonics=6)
    salience, loudness = bass_salience(bass, SR)
    distributions, strengths = bass_per_beat(salience, loudness, [0.0, 1.0, 2.0], SR)
    assert distributions[0].argmax() == NOTE["A"]
    assert strengths[0] > 0.5


def test_downbeat_flags_mark_bar_starts():
    from analysis.stem_chords import downbeat_flags

    times = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]
    flags = downbeat_flags(times, [0.02, 2.0])
    assert flags.tolist() == [True, False, False, False, True]
    assert not downbeat_flags(times, []).any()


# --- when stems are used -------------------------------------------------------


@pytest.fixture
def separation(monkeypatch):
    from analysis import stems

    calls = []
    monkeypatch.setattr(stems, "stems_available", lambda: True)
    monkeypatch.setattr(stems, "content_key", lambda path: "key")
    monkeypatch.setattr(stems, "find_cached", lambda key: (None, None))
    monkeypatch.setattr(
        stems, "separate", lambda path, key=None: calls.append(path) or {"bass": 1}
    )
    monkeypatch.delenv("SECTIONIST_STEMS", raising=False)
    return stems, calls


def test_chords_use_stems_by_default(separation):
    from analysis.stem_chords import stems_for_chords

    _stems, calls = separation
    assert stems_for_chords("song.mp3") == {"bass": 1}
    assert calls == ["song.mp3"]


def test_chords_reuse_stems_already_split(separation, monkeypatch):
    from analysis.stem_chords import stems_for_chords

    stems, calls = separation
    monkeypatch.setattr(stems, "find_cached", lambda key: ("htdemucs_6s", {"bass": 2}))
    assert stems_for_chords("song.mp3") == {"bass": 2}
    assert calls == []


def test_switching_stems_off_reads_chords_from_the_mix(separation, monkeypatch):
    from analysis.stem_chords import stems_for_chords

    _stems, calls = separation
    monkeypatch.setenv("SECTIONIST_STEMS", "off")
    assert stems_for_chords("song.mp3") is None
    assert calls == []


def test_engine_falls_back_to_the_mix_and_says_which(monkeypatch):
    from analysis import librosa_engine
    from analysis.librosa_engine import LibrosaAnalyzer

    result = {"chords": ["mix"], "duration": 10.0}
    monkeypatch.setattr(librosa_engine, "chords_for_file", lambda *a: None)
    LibrosaAnalyzer.add_stem_chords("song.mp3", result)
    assert result == {"chords": ["mix"], "duration": 10.0, "chord_source": "mix"}

    def broken(*args):
        raise RuntimeError("no GPU memory")

    monkeypatch.setattr(librosa_engine, "chords_for_file", broken)
    LibrosaAnalyzer.add_stem_chords("song.mp3", result)
    assert result["chords"] == ["mix"] and result["chord_source"] == "mix"

    stem_chords = [{"name": "Am", "start": 0.0, "end": 9.0}]
    stem_chords.append({"name": "C", "start": 9.0, "end": 12.0})  # past the end
    monkeypatch.setattr(librosa_engine, "chords_for_file", lambda *a: stem_chords)
    LibrosaAnalyzer.add_stem_chords("song.mp3", result)
    assert result["chords"] == stem_chords[:1]
    assert result["chord_source"] == "stems"


def test_server_passes_downbeats_lyrics_and_chord_source():
    import server

    analysis = {
        "duration": 4.0,
        "tempo": 120.0,
        "key": "C major",
        "key_changes": [],
        "sections": [],
        "beats_detected": 8,
        "chords": [],
        "chord_source": "stems",
        "downbeats": [0.0, 2.0],
        "lyrics": [{"start": 0.0, "end": 1.0, "text": "hello"}],
    }
    server.app.config["TESTING"] = True
    with patch("server.analyze_audio_file", return_value=analysis):
        with server.app.test_client() as client:
            data = {"audio": (io.BytesIO(b"RIFF"), "song.wav")}
            reply = client.post(
                "/analyze", data=data, content_type="multipart/form-data"
            )
    body = reply.get_json()["analysis"]
    assert body["chord_source"] == "stems"
    assert body["downbeats"] == [0.0, 2.0]
    assert body["lyrics"][0]["text"] == "hello"
