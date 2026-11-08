"""Geometry, colours and painting for the chord track.

Kept out of the timeline widget so the chord lane stays small enough to reason
about, and so its geometry can be tested without a window.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPen

CHORD_LANE_HEIGHT = 30

PITCH_CLASSES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

CHORD_PALETTE = (
    "#4E79A7",
    "#F28E2B",
    "#E15759",
    "#76B7B2",
    "#59A14F",
    "#EDC948",
    "#B07AA1",
    "#FF9DA7",
    "#9C755F",
    "#BAB0AC",
    "#86BCB6",
    "#D37295",
)

FALLBACK_COLOR = QColor(138, 138, 138)


def chord_color(name):
    """Colour a chord by its root, darker for minor."""
    text = str(name).strip()
    minor = False
    if text.endswith("m7"):
        text, minor = text[:-2], True
    elif text.endswith("maj7"):
        text = text[:-4]
    elif text.endswith("7"):
        text = text[:-1]
    elif text.endswith("m"):
        text, minor = text[:-1], True

    try:
        color = QColor(CHORD_PALETTE[PITCH_CLASSES.index(text)])
    except ValueError:
        return QColor(FALLBACK_COLOR)
    return color.darker(125) if minor else color


def chord_at_position(chords, duration, width, x):
    """Index of the chord under ``x``, or -1."""
    if not chords or duration <= 0 or width <= 0:
        return -1
    timestamp = (x / width) * duration
    for index, chord in enumerate(chords):
        if chord.get("start", 0) <= timestamp <= chord.get("end", 0):
            return index
    return -1


def chord_boundary_at(chords, duration, width, x, tolerance=6):
    """Index of the boundary between chord ``i`` and ``i+1`` near ``x``."""
    if len(chords) < 2 or duration <= 0 or width <= 0:
        return -1
    for index in range(len(chords) - 1):
        edge = int((chords[index].get("end", 0) / duration) * width)
        if abs(x - edge) <= tolerance:
            return index
    return -1


def paint_chord_track(painter, chords, duration, width, height, selected=-1):
    """Draw the chord lane along the bottom of the widget."""
    if not chords or duration <= 0:
        return

    lane_top = height - CHORD_LANE_HEIGHT
    painter.fillRect(0, lane_top, width, CHORD_LANE_HEIGHT, QColor(38, 38, 38))
    painter.setPen(QPen(QColor(120, 120, 120), 1))
    painter.drawLine(0, lane_top, width, lane_top)
    painter.setFont(QFont("Arial", 9))

    for index, chord in enumerate(chords):
        start = float(chord.get("start", 0))
        end = float(chord.get("end", 0))
        name = chord.get("name", "")
        if end <= start:
            continue

        x1 = int((start / duration) * width)
        x2 = int((end / duration) * width)
        block_width = max(1, x2 - x1)
        block = (x1, lane_top + 3, block_width, CHORD_LANE_HEIGHT - 6)

        painter.fillRect(block[0], block[1], block[2], block[3], chord_color(name))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(block[0], block[1], block[2], block[3])

        if block_width >= 22:
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(
                block[0],
                block[1],
                block[2],
                block[3],
                Qt.AlignmentFlag.AlignCenter,
                name,
            )

        if index == selected:
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawRect(block[0], block[1], block[2], block[3])
