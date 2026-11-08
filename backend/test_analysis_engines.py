"""Tests for the pluggable analysis engines.

These run without torch installed: the SongFormer engine imports it lazily and
the registry reports it as unavailable.
"""

import pytest

from analysis import EngineUnavailable, available_engines, get_analyzer
from analysis.librosa_engine import LibrosaAnalyzer
from analysis.sections import display_names, merge_consecutive, to_sections
from analysis.songformer_engine import SongFormerAnalyzer, resolve_device

# --- section post-processing -------------------------------------------------


def test_merge_consecutive_collapses_repeats():
    segments = [
        {"start": 0.0, "end": 10.0, "label": "verse"},
        {"start": 10.0, "end": 20.0, "label": "verse"},
        {"start": 20.0, "end": 30.0, "label": "chorus"},
    ]

    merged = merge_consecutive(segments)

    assert len(merged) == 2
    assert merged[0]["start"] == 0.0
    assert merged[0]["end"] == 20.0
    assert merged[1]["label"] == "chorus"


def test_merge_consecutive_does_not_mutate_input():
    segments = [{"start": 0.0, "end": 5.0, "label": "intro"}]

    merge_consecutive(segments)

    assert segments[0]["end"] == 5.0


def test_display_names_numbers_repeats():
    assert display_names(["verse", "verse", "chorus"]) == [
        "Verse 1",
        "Verse 2",
        "Chorus",
    ]


def test_display_names_handles_special_labels():
    assert display_names(["pre-chorus", "inst", "silence"]) == [
        "Pre-Chorus",
        "Instrumental",
        "Silence",
    ]


def test_to_sections_drops_slivers_and_merges_neighbours():
    raw = [
        {"start": 0.0, "end": 20.0, "label": "intro"},
        {"start": 20.0, "end": 20.4, "label": "verse"},  # too short, dropped
        {"start": 20.4, "end": 40.0, "label": "verse"},
        {"start": 40.0, "end": 60.0, "label": "chorus"},
    ]

    sections = to_sections(raw)

    assert [section["name"] for section in sections] == ["Intro", "Verse", "Chorus"]
    assert sections[1]["start"] == 20.4
    # Model output has no per-section confidence, so none is invented.
    assert all("confidence" not in section for section in sections)


def test_to_sections_rounds_timestamps():
    sections = to_sections([{"start": 0.123456, "end": 12.345678, "label": "verse"}])

    assert sections[0]["start"] == 0.12
    assert sections[0]["end"] == 12.35


# --- engine registry ---------------------------------------------------------


def test_available_engines_always_includes_librosa(monkeypatch):
    monkeypatch.setattr("analysis.songformer_available", lambda: False)

    assert available_engines() == ["librosa"]


def test_auto_falls_back_to_librosa(monkeypatch):
    monkeypatch.setattr("analysis.songformer_available", lambda: False)
    monkeypatch.delenv("SECTIONIST_ENGINE", raising=False)

    assert isinstance(get_analyzer(), LibrosaAnalyzer)


def test_auto_prefers_songformer_when_installed(monkeypatch):
    monkeypatch.setattr("analysis.songformer_available", lambda: True)
    monkeypatch.delenv("SECTIONIST_ENGINE", raising=False)

    assert isinstance(get_analyzer(), SongFormerAnalyzer)


def test_engine_can_be_forced_by_name(monkeypatch):
    monkeypatch.setattr("analysis.songformer_available", lambda: True)

    assert isinstance(get_analyzer("librosa"), LibrosaAnalyzer)
    assert isinstance(get_analyzer("songformer"), SongFormerAnalyzer)


def test_engine_can_be_forced_by_environment(monkeypatch):
    monkeypatch.setattr("analysis.songformer_available", lambda: False)
    monkeypatch.setenv("SECTIONIST_ENGINE", "librosa")

    assert isinstance(get_analyzer(), LibrosaAnalyzer)


def test_unavailable_engine_raises_actionable_error(monkeypatch):
    monkeypatch.setattr("analysis.songformer_available", lambda: False)

    with pytest.raises(EngineUnavailable, match="requirements-songformer"):
        get_analyzer("songformer")


def test_unknown_engine_raises():
    with pytest.raises(EngineUnavailable, match="Unknown engine"):
        get_analyzer("definitely-not-an-engine")


# --- device policy -----------------------------------------------------------


def test_explicit_device_wins(monkeypatch):
    monkeypatch.setenv("SECTIONIST_DEVICE", "mps")

    assert resolve_device() == "mps"


def test_constructor_does_not_import_torch(monkeypatch):
    # Constructing the engine must stay cheap and work without torch installed.
    engine = SongFormerAnalyzer(directory="/nonexistent", device="cpu")

    assert engine.device == "cpu"
