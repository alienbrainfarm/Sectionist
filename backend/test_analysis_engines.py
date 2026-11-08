"""Tests for the pluggable analysis engines.

These run without torch installed: the SongFormer engine imports it lazily and
the registry reports it as unavailable.
"""

import numpy as np
import pytest

from analysis import EngineUnavailable, available_engines, get_analyzer
from analysis.librosa_engine import LibrosaAnalyzer
from analysis.calibration import (
    CLASS_ORDER,
    SoftmaxRegression,
    apply_calibration,
    canonical_label,
    load_corrections,
    reduce_probabilities,
    section_features,
)
from analysis.sections import (
    display_names,
    merge_consecutive,
    snap_boundaries,
    to_sections,
)
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


# --- confidence --------------------------------------------------------------


def test_merge_consecutive_combines_confidence_weighted():
    segments = [
        {"start": 0.0, "end": 30.0, "label": "verse", "confidence": 0.9},
        {"start": 30.0, "end": 40.0, "label": "verse", "confidence": 0.4},
    ]

    merged = merge_consecutive(segments)

    assert len(merged) == 1
    # 30s at 0.9 and 10s at 0.4 -> 0.775
    assert merged[0]["confidence"] == pytest.approx(0.775)


def test_to_sections_carries_confidence():
    sections = to_sections(
        [{"start": 0.0, "end": 10.0, "label": "chorus", "confidence": 0.8123}]
    )

    assert sections[0]["confidence"] == 0.812


# --- downbeat snapping -------------------------------------------------------


def test_snap_boundaries_moves_to_nearby_downbeat():
    sections = [
        {"name": "Intro", "start": 0.0, "end": 15.9},
        {"name": "Verse", "start": 15.9, "end": 32.1},
    ]
    downbeats = [0.0, 16.0, 32.0, 48.0]

    snapped = snap_boundaries(sections, downbeats)

    assert snapped[0]["end"] == 16.0
    assert snapped[1]["start"] == 16.0
    assert snapped[1]["end"] == 32.0


def test_snap_boundaries_ignores_distant_downbeats():
    sections = [
        {"name": "Intro", "start": 0.0, "end": 20.0},
        {"name": "Verse", "start": 20.0, "end": 40.0},
    ]
    downbeats = [0.0, 16.0, 32.0]

    snapped = snap_boundaries(sections, downbeats)

    assert snapped[0]["end"] == 20.0


def test_snap_boundaries_never_inverts_order():
    sections = [
        {"name": "A", "start": 0.0, "end": 10.1},
        {"name": "B", "start": 10.1, "end": 10.4},
        {"name": "C", "start": 10.4, "end": 20.0},
    ]
    downbeats = [0.0, 10.2, 20.0]

    snapped = snap_boundaries(sections, downbeats)

    starts = [section["start"] for section in snapped]
    assert starts == sorted(starts)
    assert all(
        section["end"] > section["start"] for section in snapped
    ), "sections must stay positive-length"


def test_snap_boundaries_without_grid_is_a_noop():
    sections = [{"name": "A", "start": 0.0, "end": 12.3}]

    assert snap_boundaries(sections, []) == sections


def test_beats_unavailable_returns_none(monkeypatch):
    from analysis.beats import detect_beats

    monkeypatch.setattr("analysis.beats.beats_available", lambda: False)

    assert detect_beats("whatever.mp3") == (None, None)


# --- label model -------------------------------------------------------------


def test_canonical_label_normalises_display_names():
    assert canonical_label("Verse 2") == "verse"
    assert canonical_label("Pre-Chorus") == "pre-chorus"
    assert canonical_label("Instrumental") == "inst"
    assert canonical_label("  CHORUS 1 ") == "chorus"


def test_reduce_probabilities_keeps_canonical_classes():
    id_to_label = {0: "intro", 1: "verse", 2: "chorus", 3: "inst", 8: "prechorus"}
    probabilities = np.zeros((2, 9))
    probabilities[:, 2] = 0.5  # chorus
    probabilities[:, 8] = 0.25  # prechorus alias
    probabilities[:, 0] = 0.25  # intro

    reduced = reduce_probabilities(probabilities, id_to_label)

    assert reduced.shape == (2, len(CLASS_ORDER))
    assert reduced.sum(axis=1).tolist() == [1.0, 1.0]
    assert reduced[0, CLASS_ORDER.index("chorus")] == 0.5
    assert reduced[0, CLASS_ORDER.index("pre-chorus")] == 0.25


def test_section_features_shape_and_position():
    probabilities = np.full((100, len(CLASS_ORDER)), 1 / len(CLASS_ORDER))
    segments = [
        {"start": 0.0, "end": 5.0},
        {"start": 5.0, "end": 20.0},
    ]

    features = section_features(probabilities, 10, segments, duration=20.0)

    assert features.shape == (2, len(CLASS_ORDER) + 5)
    # relative position of the second section
    assert features[1, len(CLASS_ORDER) + 1] == 0.25


def test_softmax_regression_learns_a_separable_problem():
    rng = np.random.default_rng(0)
    features = np.vstack([rng.normal(0.0, 0.1, (30, 4)), rng.normal(3.0, 0.1, (30, 4))])
    targets = [0] * 30 + [1] * 30

    model = SoftmaxRegression(epochs=400).fit(features, targets)

    predicted = model.predict_proba(features).argmax(axis=1)
    assert (predicted == np.array(targets)).mean() > 0.95


def test_softmax_regression_round_trips(tmp_path):
    rng = np.random.default_rng(1)
    features = rng.normal(size=(20, 3))
    targets = [index % 2 for index in range(20)]
    model = SoftmaxRegression(epochs=50).fit(features, targets)

    path = tmp_path / "model.npz"
    model.save(path)
    restored = SoftmaxRegression.load(path)

    assert np.allclose(model.predict_proba(features), restored.predict_proba(features))


def test_apply_calibration_overrides_labels():
    class FixedModel:
        def predict_proba(self, features):
            distribution = np.zeros((len(features), len(CLASS_ORDER)))
            distribution[:, CLASS_ORDER.index("pre-chorus")] = 0.9
            distribution[:, CLASS_ORDER.index("chorus")] = 0.1
            return distribution

    segments = [{"start": 0.0, "end": 10.0, "label": "chorus"}]
    probabilities = np.full((100, len(CLASS_ORDER)), 1 / len(CLASS_ORDER))

    apply_calibration(segments, probabilities, 10, FixedModel(), duration=10.0)

    assert segments[0]["label"] == "pre-chorus"
    assert segments[0]["confidence"] == pytest.approx(0.9)


def test_load_corrections_reads_saved_analysis(tmp_path):
    import json

    path = tmp_path / "analysis.json"
    path.write_text(
        json.dumps(
            {
                "success": True,
                "analysis": {
                    "sections": [
                        {"name": "Verse 1", "start": 0.0, "end": 12.0},
                        {"name": "Pre-Chorus", "start": 12.0, "end": 24.0},
                    ]
                },
            }
        )
    )

    sections = load_corrections(path)

    assert [section["label"] for section in sections] == ["verse", "pre-chorus"]


# --- beat enrichment ---------------------------------------------------------


def test_add_beats_attaches_count_and_grid():
    from analysis.librosa_engine import LibrosaAnalyzer

    result = {}
    LibrosaAnalyzer.add_beats(
        "song.mp3", result, beats=[0.5, 1.0, 1.5], downbeats=[0.5, 2.5]
    )

    assert result["beats_detected"] == 3
    assert result["downbeats"] == [0.5, 2.5]


def test_add_beats_is_a_noop_without_the_optional_model(monkeypatch):
    from analysis.librosa_engine import LibrosaAnalyzer

    monkeypatch.setattr("analysis.librosa_engine.beats_available", lambda: False)
    result = {"beats_detected": 7}

    LibrosaAnalyzer.add_beats("song.mp3", result)

    assert result == {"beats_detected": 7}
    assert "downbeats" not in result


def test_librosa_engine_can_skip_heuristic_segmentation(monkeypatch):
    from analysis.librosa_engine import LibrosaAnalyzer

    seen = {}

    def fake_analyze(path, include_sections=True):
        seen["include_sections"] = include_sections
        return {
            "duration": 1.0,
            "tempo": 120.0,
            "key": "C major",
            "key_changes": [],
            "sections": [],
            "beats_detected": 0,
            "chords": [],
        }

    monkeypatch.setattr("example.analyze_audio_file", fake_analyze)
    monkeypatch.setattr("analysis.librosa_engine.beats_available", lambda: False)

    result = LibrosaAnalyzer().analyze("song.mp3", include_sections=False)

    assert seen["include_sections"] is False
    assert result["sections"] == []


# --- lyrics ------------------------------------------------------------------


def test_add_lyrics_attaches_lines():
    from analysis.librosa_engine import LibrosaAnalyzer

    result = {}
    lines = [{"start": 0.0, "end": 1.0, "text": "hello"}]

    LibrosaAnalyzer.add_lyrics("song.mp3", result, lines=lines)

    assert result["lyrics"] == lines


def test_add_lyrics_is_a_noop_without_the_optional_package(monkeypatch):
    from analysis.librosa_engine import LibrosaAnalyzer

    monkeypatch.setattr("analysis.librosa_engine.lyrics_available", lambda: False)
    result = {"duration": 12.0}

    LibrosaAnalyzer.add_lyrics("song.mp3", result)

    assert "lyrics" not in result


# --- vocal separation --------------------------------------------------------


def test_stems_enabled_by_default(monkeypatch):
    from analysis import stems

    monkeypatch.delenv("SECTIONIST_STEMS", raising=False)
    monkeypatch.setattr(stems, "stems_available", lambda: True)

    assert stems.enabled() is True


def test_stems_can_be_switched_off(monkeypatch):
    from analysis import stems

    monkeypatch.setattr(stems, "stems_available", lambda: True)
    for setting in ("off", "0", "false"):
        monkeypatch.setenv("SECTIONIST_STEMS", setting)
        assert stems.enabled() is False


def test_stems_need_the_package_even_when_switched_on(monkeypatch):
    from analysis import stems

    monkeypatch.setenv("SECTIONIST_STEMS", "1")
    monkeypatch.setattr(stems, "stems_available", lambda: False)

    assert stems.enabled() is False


def test_vocals_path_is_none_when_disabled(monkeypatch):
    from analysis import stems

    monkeypatch.setenv("SECTIONIST_STEMS", "off")

    assert stems.vocals_path("song.mp3") is None


def test_transcribe_prefers_the_vocal_stem(monkeypatch):
    from analysis import lyrics

    seen = {}

    class FakeModel:
        def transcribe(self, path, vad_filter=False):
            seen["path"] = path
            seen["vad"] = vad_filter
            return [], None

    monkeypatch.setattr(lyrics, "lyrics_available", lambda: True)
    monkeypatch.setattr(lyrics, "_get_model", lambda: FakeModel())
    monkeypatch.setattr(lyrics, "vocals_path", lambda path: "/tmp/vocals.wav")

    lyrics.transcribe("song.mp3")

    assert seen["path"] == "/tmp/vocals.wav"
    assert seen["vad"] is False


def test_transcribe_falls_back_to_the_mix(monkeypatch):
    from analysis import lyrics

    seen = {}

    class FakeModel:
        def transcribe(self, path, vad_filter=False):
            seen["path"] = path
            return [], None

    monkeypatch.setattr(lyrics, "lyrics_available", lambda: True)
    monkeypatch.setattr(lyrics, "_get_model", lambda: FakeModel())
    monkeypatch.setattr(lyrics, "vocals_path", lambda path: None)

    lyrics.transcribe("song.mp3")

    assert seen["path"] == "song.mp3"
