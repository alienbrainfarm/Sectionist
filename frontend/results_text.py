"""Rich-text rendering for the analysis details panel.

Kept out of the main window so the window stays a coordinator rather than a
template engine, and so the wording can be tested without a QApplication.
"""

from html import escape

try:
    from .theme import TEXT, TEXT_DIM
    from .chord_track import chord_color
except ImportError:
    from theme import TEXT, TEXT_DIM
    from chord_track import chord_color


def _timestamp(seconds):
    seconds = max(0, int(float(seconds or 0)))
    return f"{seconds // 60}:{seconds % 60:02d}"


def _held_for(seconds):
    """A length of time, written so it cannot be mistaken for a timestamp."""
    seconds = max(0, round(float(seconds or 0)))
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}m {seconds:02d}s" if minutes else f"{seconds}s"


def chord_vocabulary(chords):
    """(name, total seconds) for each chord, most-used first."""
    totals = {}
    for chord in chords or []:
        name = str(chord.get("name", "")).strip()
        if not name:
            continue
        length = float(chord.get("end", 0)) - float(chord.get("start", 0))
        totals[name] = totals.get(name, 0.0) + max(0.0, length)
    return sorted(totals.items(), key=lambda item: (-item[1], item[0]))


def _stat(label, value):
    return (
        f'<td style="padding:4px 18px 8px 0;">'
        f'<div style="color:{TEXT_DIM}; font-size:8pt;">{escape(label)}</div>'
        f'<div style="color:{TEXT}; font-size:12pt; font-weight:600;">'
        f"{escape(str(value))}</div></td>"
    )


def _heading(text):
    return (
        f'<p style="color:{TEXT_DIM}; font-size:8pt; font-weight:600;'
        f' margin:14px 0 4px 0;">{escape(text.upper())}</p>'
    )


def format_details(analysis):
    """Render the analysis details panel as HTML."""
    downbeats = analysis.get("downbeats") or []
    stats = [
        ("Key", analysis.get("key", "Unknown")),
        ("Tempo", f"{float(analysis.get('tempo', 0) or 0):.1f} BPM"),
        ("Duration", _timestamp(analysis.get("duration", 0))),
        ("Bars", len(downbeats) if downbeats else "—"),
        ("Beats", analysis.get("beats_detected", 0)),
        ("Engine", analysis.get("engine", "librosa")),
    ]
    rows = [stats[:3], stats[3:]]
    html = '<table cellspacing="0" cellpadding="0">'
    for row in rows:
        html += "<tr>" + "".join(_stat(label, value) for label, value in row)
        html += "</tr>"
    html += "</table>"

    key_changes = analysis.get("key_changes", [])
    if key_changes:
        html += _heading("Key changes")
        for change in key_changes:
            html += (
                f'<div style="margin:2px 0;">'
                f'<span style="color:{TEXT_DIM};">'
                f"{_timestamp(change.get('timestamp', 0))}</span>&nbsp;&nbsp;"
                f"{escape(str(change.get('from_key', 'Unknown')))} → "
                f"<b>{escape(str(change.get('to_key', 'Unknown')))}</b></div>"
            )

    chords = analysis.get("chords", [])
    vocabulary = chord_vocabulary(chords)
    if vocabulary:
        source = " · from stems" if analysis.get("chord_source") == "stems" else ""
        html += _heading(f"Chords used · time held{source} ({len(chords)} changes)")
        chips = []
        for name, seconds in vocabulary:
            color = chord_color(name).name()
            chips.append(
                f'<span style="background:{color}; color:#111318;'
                f' font-weight:600;">&nbsp;{escape(name)}&nbsp;</span>'
                f'<span style="color:{TEXT_DIM};">&nbsp;{_held_for(seconds)}</span>'
            )
        html += (
            '<p style="line-height:170%;">' + "&nbsp;&nbsp;&nbsp; ".join(chips) + "</p>"
        )

    return html
