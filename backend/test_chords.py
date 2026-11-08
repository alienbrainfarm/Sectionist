"""Tests for beat-synchronous chord recognition."""

import librosa
import numpy as np
import pytest

from analysis.chords import (
    build_templates,
    chord_name,
    detect_chords,
    merge_runs,
    viterbi,
)

SAMPLE_RATE = 22050


def test_chord_names():
    assert chord_name(0, "maj") == "C"
    assert chord_name(9, "min") == "Am"
    assert chord_name(9, "7") == "A7"


def test_templates_are_unit_length_and_correct():
    names, templates = build_templates(("maj", "min"))

    assert len(names) == 24
    assert np.allclose(np.linalg.norm(templates, axis=1), 1.0)

    c_major = templates[names.index("C")]
    assert set(np.flatnonzero(c_major)) == {0, 4, 7}  # C, E, G

    a_minor = templates[names.index("Am")]
    assert set(np.flatnonzero(a_minor)) == {9, 0, 4}  # A, C, E


def test_viterbi_prefers_staying_put_on_ambiguous_evidence():
    emissions = np.array([[0.0, -0.1], [-0.1, 0.0]])

    assert viterbi(emissions, self_transition=0.99) == [0, 0]


def test_merge_runs_drops_slivers():
    path = [0, 1, 0]
    names = ["C", "G"]
    confidences = [0.9, 0.5, 0.8]
    times = np.array([0.0, 1.0, 1.1, 2.0])

    chords = merge_runs(path, names, confidences, times, min_duration=0.3)

    assert [chord["name"] for chord in chords] == ["C", "C"]
    assert chords[0]["end"] == 1.0


def triad(root, minor, duration, sr=SAMPLE_RATE):
    """Major or minor triad, with a 120 BPM click so beats can be tracked."""
    time = np.arange(int(sr * duration)) / sr
    third = 3 if minor else 4
    frequencies = [
        librosa.midi_to_hz(60 + root),
        librosa.midi_to_hz(60 + root + third),
        librosa.midi_to_hz(60 + root + 7),
    ]
    chord = 0.25 * sum(np.sin(2 * np.pi * f * time) for f in frequencies) / 3
    click = 0.05 * np.sin(2 * np.pi * 1000 * time) * (time % 0.5 < 0.02)
    return chord + click


def test_recovers_a_known_progression():
    progression = [(0, False, "C"), (7, False, "G"), (9, True, "Am"), (5, False, "F")]
    audio = np.concatenate([triad(root, minor, 4.0) for root, minor, _ in progression])

    chords = detect_chords(audio, SAMPLE_RATE, hop_length=512)

    assert [chord["name"] for chord in chords] == [name for *_, name in progression]
    # Boundaries should land on the section edges (4, 8, 12 seconds).
    for chord, expected in zip(chords[1:], [4.0, 8.0, 12.0]):
        assert chord["start"] == pytest.approx(expected, abs=0.6)
    assert all(chord["confidence"] > 0.8 for chord in chords)


def test_confidence_is_a_match_score():
    audio = triad(0, False, 4.0)

    chords = detect_chords(audio, SAMPLE_RATE, hop_length=512)

    assert chords
    assert 0.0 <= chords[0]["confidence"] <= 1.0
    assert chords[0]["confidence"] > 0.8
