"""Windowing helpers for running the model over long audio.

Apple's MPS backend is roughly three times faster than CPU on short inputs and
then collapses on long ones: around 200 seconds of audio it starts swapping and
ends up slower than the CPU. Splitting a track into overlapping windows keeps
each forward pass in the fast regime.

Overlap exists so the seam is not a hard cut. Each window's *core* is the part
of it that no other window covers, and only predictions touching the core are
kept. That way every second of the song is predicted by a window in which it is
not an edge case.
"""


def chunk_bounds(duration, window=90.0, overlap=20.0):
    """Split ``duration`` into overlapping ``(start, end)`` windows."""
    if duration <= window:
        return [(0.0, duration)]

    hop = window - overlap
    bounds = []
    start = 0.0
    while True:
        end = min(start + window, duration)
        bounds.append((start, end))
        if end >= duration:
            break
        start += hop
    return bounds


def core_bounds(index, start, end, duration, overhead=20.0):
    """The part of a window whose predictions are kept.

    The first window keeps from 0 and the last keeps to the end, so the cores
    tile the song exactly with no gaps.
    """
    left = 0.0 if index == 0 else start + overhead / 2
    right = duration if end >= duration else end - overhead / 2
    return left, right


def trim_segments(segments, offset, core_start, core_end):
    """Shift window-relative segments to absolute time and clip to the core.

    Segments that do not overlap the core are dropped entirely; the window that
    owns that region will have predicted them from a better vantage point.
    """
    kept = []
    for segment in segments:
        start = offset + float(segment["start"])
        end = offset + float(segment["end"])
        if end <= core_start or start >= core_end:
            continue
        kept.append(
            {
                "start": max(start, core_start),
                "end": min(end, core_end),
                "label": segment.get("label", "unknown"),
            }
        )
    return kept
