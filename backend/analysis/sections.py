"""Post-processing for predicted song sections.

SongFormer predicts boundaries and labels with independent heads, so it emits a
boundary wherever it hears a change even when the label does not change (a
repeated verse, for example). Those runs have to be merged before the sections
are useful, and the labels need to be turned into the names the UI expects.
"""

from collections import Counter, defaultdict

# Model labels that need more than title-casing.
LABEL_DISPLAY = {
    "pre-chorus": "Pre-Chorus",
    "post-chorus": "Post-Chorus",
    "inst": "Instrumental",
    "silence": "Silence",
}


def _duration(segment):
    return float(segment["end"]) - float(segment["start"])


def merge_consecutive(segments):
    """Merge neighbouring segments that carry the same label.

    ``segments`` is a list of dicts with ``start``, ``end`` and ``label``, and
    optionally ``confidence``. Confidences are combined as a duration-weighted
    mean so a long confident section is not dragged down by a short one.
    """
    merged = []
    for segment in segments:
        if merged and merged[-1]["label"] == segment["label"]:
            previous = merged[-1]
            if "confidence" in previous and "confidence" in segment:
                total = _duration(previous) + _duration(segment)
                previous["confidence"] = (
                    previous["confidence"] * _duration(previous)
                    + segment["confidence"] * _duration(segment)
                ) / total
            previous["end"] = segment["end"]
        else:
            merged.append(dict(segment))
    return merged


def display_names(labels):
    """Turn model labels into display names, numbering repeats.

    ``["verse", "verse", "chorus"]`` becomes ``["Verse 1", "Verse 2", "Chorus"]``.
    """
    counts = Counter(labels)
    seen = defaultdict(int)
    names = []
    for label in labels:
        pretty = LABEL_DISPLAY.get(label, label.replace("-", " ").title())
        if counts[label] > 1:
            seen[label] += 1
            pretty = f"{pretty} {seen[label]}"
        names.append(pretty)
    return names


def prepare_segments(segments, min_duration=1.0):
    """Drop slivers and merge neighbouring segments with the same label."""
    kept = [
        dict(segment)
        for segment in segments
        if float(segment["end"]) - float(segment["start"]) >= min_duration
    ]
    for segment in kept:
        segment["label"] = str(segment.get("label", "unknown")).lower().strip()

    return merge_consecutive(kept)


def finalize_sections(segments):
    """Turn prepared segments into the API section shape."""
    names = display_names([segment["label"] for segment in segments])

    sections = []
    for name, segment in zip(names, segments):
        section = {
            "name": name,
            "start": round(float(segment["start"]), 2),
            "end": round(float(segment["end"]), 2),
        }
        if "confidence" in segment:
            section["confidence"] = round(float(segment["confidence"]), 3)
        sections.append(section)
    return sections


def to_sections(segments, min_duration=1.0):
    """Prepare and finalise in one step."""
    return finalize_sections(prepare_segments(segments, min_duration))


def snap_boundaries(sections, downbeats, tolerance=0.35):
    """Snap section boundaries onto the nearest downbeat.

    Only boundaries within ``tolerance`` seconds move, and ordering is
    preserved: a snap that would cross a neighbouring boundary is discarded.
    """
    if not sections or not downbeats:
        return sections

    grid = sorted(float(value) for value in downbeats)
    boundaries = [float(sections[0]["start"])] + [
        float(section["end"]) for section in sections
    ]

    snapped = [boundaries[0]]
    for index in range(1, len(boundaries)):
        value = boundaries[index]
        nearest = min(grid, key=lambda beat: abs(beat - value))
        if abs(nearest - value) <= tolerance:
            snapped.append(round(nearest, 2))
        else:
            snapped.append(value)

    # Never let a snap invert the order of two boundaries.
    for index in range(1, len(snapped)):
        if snapped[index] <= snapped[index - 1]:
            snapped[index] = boundaries[index]

    result = []
    for index, section in enumerate(sections):
        updated = dict(section)
        updated["start"] = round(snapped[index], 2)
        updated["end"] = round(snapped[index + 1], 2)
        result.append(updated)
    return result
