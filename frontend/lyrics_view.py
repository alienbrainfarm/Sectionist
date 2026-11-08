"""Formatting helpers for the lyrics panel."""


def _section_index(sections, timestamp):
    if not sections:
        return None
    for index, section in enumerate(sections):
        if float(section.get("start", 0)) <= timestamp < float(section.get("end", 0)):
            return index
    return None


def format_lyrics(lines, sections=None, gap=2.0):
    """Join transcribed lines into stanzas separated by blank lines.

    A break happens when the line falls in a different song section, which is
    what gives the panel its verse/chorus shape. Whisper emits contiguous
    lines with no silence between them, so pauses alone are not enough; the
    ``gap`` fallback only matters when sections are unavailable.

    Timestamps are deliberately not shown: the panel is for reading, and the
    section and chord tracks already carry the timing.
    """
    blocks = []
    previous_end = None
    previous_section = None
    lines_in_stanza = 0

    for line in lines:
        text = str(line.get("text", "")).strip()
        if not text:
            continue

        start = float(line.get("start", 0) or 0)
        index = _section_index(sections, start)

        if blocks:
            changed_section = (
                index is not None
                and previous_section is not None
                and index != previous_section
            )
            long_pause = previous_end is not None and start - previous_end > gap
            # Never leave a one-line orphan: sections from the heuristic engine
            # can be wrong, and a bad boundary should not fragment a line.
            if (changed_section or long_pause) and lines_in_stanza >= 2:
                blocks.append("")
                lines_in_stanza = 0

        blocks.append(text)
        lines_in_stanza += 1
        previous_end = float(line.get("end", start) or start)
        previous_section = index

    return "\n".join(blocks)


NO_TRANSCRIBER = (
    "The backend can't transcribe lyrics.\n\n"
    "On the machine running the backend, install faster-whisper:\n"
    "    pip install -r backend/requirements-lyrics.txt\n"
    "then restart the server and analyse again."
)
NO_VOCALS = "No sung words were found in this song."
NO_LYRICS = (  # an older backend that does not say whether it can transcribe
    "No lyrics came back from this analysis: either an instrumental, or the "
    "backend lacks faster-whisper (backend/requirements-lyrics.txt on the "
    "machine running it)."
)


def missing_lyrics_reason(analysis):
    available = analysis.get("lyrics_available")
    if available is None:
        return NO_LYRICS
    return NO_VOCALS if available else NO_TRANSCRIBER


def show_lyrics(dock, text, action, analysis, sections):
    """Fill the lyrics panel after an analysis and show it.

    The panel opens after every analysis, saying why when there are no
    lyrics, so a missing transcriber is not mistaken for a missing feature.
    With no analysis (a song just opened or closed) it is only cleared.
    """
    lyrics = analysis.get("lyrics", [])
    if lyrics:
        text.setPlainText(format_lyrics(lyrics, sections))
    elif analysis.get("sections"):
        text.setPlainText(missing_lyrics_reason(analysis))
    else:
        text.clear()
        return
    dock.show()
    action.setChecked(True)


def create_lyrics_dock(parent):
    """Build the lyrics dock and its text area, attached to ``parent``."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QDockWidget, QTextEdit

    dock = QDockWidget("Lyrics", parent)
    dock.setObjectName("LyricsDock")

    text = QTextEdit()
    text.setReadOnly(True)
    text.document().setDocumentMargin(14)
    font = text.font()
    font.setPointSizeF(font.pointSizeF() + 1)
    text.setFont(font)
    text.setPlaceholderText(
        "Lyrics appear here after an analysis with transcription enabled."
    )

    dock.setWidget(text)
    parent.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
    dock.hide()
    return dock, text
