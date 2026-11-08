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


def merge_consecutive(segments):
    """Merge neighbouring segments that carry the same label.

    ``segments`` is a list of dicts with ``start``, ``end`` and ``label``.
    """
    merged = []
    for segment in segments:
        if merged and merged[-1]["label"] == segment["label"]:
            merged[-1]["end"] = segment["end"]
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


def to_sections(segments, min_duration=1.0):
    """Convert model segments into the API section shape.

    Segments are dropped before merging, so a dropped sliver cannot leave two
    identical labels adjacent. Model output carries no per-section confidence,
    so the ``confidence`` key is omitted rather than invented.
    """
    kept = [
        dict(segment)
        for segment in segments
        if float(segment["end"]) - float(segment["start"]) >= min_duration
    ]
    for segment in kept:
        segment["label"] = str(segment.get("label", "unknown")).lower().strip()

    merged = merge_consecutive(kept)
    names = display_names([segment["label"] for segment in merged])

    return [
        {
            "name": name,
            "start": round(float(segment["start"]), 2),
            "end": round(float(segment["end"]), 2),
        }
        for name, segment in zip(names, merged)
    ]
