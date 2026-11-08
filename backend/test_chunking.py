"""Tests for the overlapping-window helpers used by MPS inference."""

from analysis.chunking import chunk_bounds, core_bounds, trim_segments


def test_short_audio_is_a_single_window():
    assert chunk_bounds(40.0, window=90.0, overlap=20.0) == [(0.0, 40.0)]


def test_windows_cover_the_track_and_overlap():
    bounds = chunk_bounds(200.0, window=90.0, overlap=20.0)

    assert bounds[0][0] == 0.0
    assert bounds[-1][1] == 200.0
    # Every gap between consecutive windows is the overlap.
    for (_, previous_end), (next_start, _) in zip(bounds, bounds[1:]):
        assert next_start < previous_end
        assert previous_end - next_start == 20.0


def test_cores_tile_the_track_without_gaps():
    duration = 200.0
    bounds = chunk_bounds(duration, window=90.0, overlap=20.0)
    cores = [
        core_bounds(index, start, end, duration, overhead=20.0)
        for index, (start, end) in enumerate(bounds)
    ]

    assert cores[0][0] == 0.0
    assert cores[-1][1] == duration
    for (_, previous_end), (next_start, _) in zip(cores, cores[1:]):
        assert next_start == previous_end


def test_trim_segments_shifts_and_clips_to_the_core():
    # Window starts at 70 s; a segment running 5-25 s inside it.
    segments = [{"start": 5.0, "end": 25.0, "label": "verse"}]

    kept = trim_segments(segments, offset=70.0, core_start=80.0, core_end=140.0)

    assert len(kept) == 1
    assert kept[0]["start"] == 80.0  # clipped at the core start
    assert kept[0]["end"] == 95.0  # 70 + 25
    assert kept[0]["label"] == "verse"


def test_trim_segments_drops_windows_outside_the_core():
    segments = [
        {"start": 0.0, "end": 5.0, "label": "intro"},  # ends before the core
        {"start": 60.0, "end": 90.0, "label": "chorus"},  # starts after the core
    ]

    kept = trim_segments(segments, offset=0.0, core_start=20.0, core_end=50.0)

    assert kept == []
