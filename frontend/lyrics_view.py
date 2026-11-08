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


def section_name(sections, index):
    return str(sections[index].get("name") or f"Section {index + 1}")


def lyrics_by_section(lines, sections):
    """Lyrics under a ``[Section]`` header per section, in song order.

    Every section gets its header, sung or not, so the text can be edited
    freely and still be matched back to the sections for the gig sheet.
    """
    if not sections:
        return format_lyrics(lines)
    groups = [[] for _ in sections]
    for line in lines:
        index = _section_index(sections, float(line.get("start", 0)))
        if index is None:  # before the first section or after the last
            first = float(sections[0].get("start", 0))
            index = 0 if float(line.get("start", 0)) < first else len(sections) - 1
        groups[index].append(line)
    blocks = []
    for index, group in enumerate(groups):
        body = format_lyrics(group) if group else ""
        blocks.append(
            f"[{section_name(sections, index)}]" + (f"\n{body}" if body else "")
        )
    return "\n\n".join(blocks)


def parse_lyrics_text(text):
    """``[(header or None, body)]`` from lyrics text with [Section] lines."""
    blocks, header, body = [], None, []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]") and len(stripped) > 2:
            if header is not None or any(part.strip() for part in body):
                blocks.append((header, "\n".join(body).strip()))
            header, body = stripped[1:-1].strip(), []
        else:
            body.append(line)
    if header is not None or any(part.strip() for part in body):
        blocks.append((header, "\n".join(body).strip()))
    return blocks


def lyrics_per_section(analysis, sections):
    """The lyrics for each section, in order, from edits if there are any.

    Blocks are matched to sections by order, which survives renaming a
    section. Text before the first header goes with the first section.
    """
    text = analysis.get("lyrics_text")
    if text is None:
        text = lyrics_by_section(analysis.get("lyrics", []), sections)
    result = [""] * len(sections)
    if not sections:
        return result
    blocks = parse_lyrics_text(text)
    if blocks and blocks[0][0] is None:
        preamble = blocks.pop(0)[1]
        if blocks:
            blocks[0] = (blocks[0][0], (preamble + "\n" + blocks[0][1]).strip())
        else:
            blocks = [(None, preamble)]
    for index, (_header, body) in enumerate(blocks[: len(sections)]):
        result[index] = body
    return result


def show_lyrics(dock, text, action, analysis, sections):
    """Fill the lyrics panel after an analysis and show it.

    The panel opens after every analysis, saying why when there are no
    lyrics, so a missing transcriber is not mistaken for a missing feature.
    With no analysis (a song just opened or closed) it is only cleared.
    """
    lyrics = analysis.get("lyrics", [])
    if analysis.get("lyrics_text") is not None:
        text.setPlainText(analysis["lyrics_text"])  # the user's edits
    elif lyrics:
        text.setPlainText(lyrics_by_section(lyrics, sections))
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
