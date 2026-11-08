"""Text rendering for the results panels.

Kept out of the main window so the window stays a coordinator rather than a
template engine, and so the wording can be tested without a QApplication.
"""


def _timestamp(seconds):
    minutes = int(float(seconds) // 60)
    remainder = int(float(seconds) % 60)
    return f"{minutes:02d}:{remainder:02d}"


def format_sections(sections):
    """Render the song sections panel."""
    text = "Song Sections:\n\n"
    for index, section in enumerate(sections, 1):
        name = section.get("name", "Unknown")
        start = section.get("start", 0)
        end = section.get("end", 0)
        confidence = section.get("confidence")

        text += f"{index}. {name}\n"
        text += f"   Time: {_timestamp(start)} - {_timestamp(end)}\n"
        if confidence is None:
            # Model-based engines do not report per-section confidence.
            text += "   Confidence: —\n\n"
        else:
            text += f"   Confidence: {confidence:.1%}\n\n"
    return text


def format_details(analysis):
    """Render the analysis details panel."""
    text = "Analysis Details:\n\n"
    text += f"Duration: {_timestamp(analysis.get('duration', 0))}\n"
    text += f"Tempo: {analysis.get('tempo', 0):.1f} BPM\n"
    text += f"Key: {analysis.get('key', 'Unknown')}\n"
    text += f"Beats Detected: {analysis.get('beats_detected', 0)}\n"
    text += f"Engine: {analysis.get('engine', 'librosa')}\n\n"

    key_changes = analysis.get("key_changes", [])
    if key_changes:
        text += "Key Changes:\n"
        for change in key_changes:
            text += (
                f"  {_timestamp(change.get('timestamp', 0))}: "
                f"{change.get('from_key', 'Unknown')} → "
                f"{change.get('to_key', 'Unknown')}\n"
            )
        text += "\n"

    chords = analysis.get("chords", [])
    if chords:
        text += f"Chords ({len(chords)}):\n"
        for chord in chords:
            text += (
                f"  {_timestamp(chord.get('start', 0))} - "
                f"{_timestamp(chord.get('end', 0))}: "
                f"{chord.get('name', 'Unknown')}\n"
            )

    return text
