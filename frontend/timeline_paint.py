"""Painting for the timeline: ruler, section blocks, playhead and overlays.

The timeline widget owns state and mouse handling; this module only draws, so
each piece can be read (and changed) without scrolling past event handlers.
All x coordinates map time linearly across the full widget width, which is
what the widget's hit testing assumes.
"""

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainterPath, QPen, QPolygonF

try:
    from .theme import (
        ACCENT,
        BORDER,
        PLAYHEAD,
        SURFACE,
        TEXT_DIM,
        TEXT_FAINT,
        section_color,
        text_color_on,
        ui_font,
    )
except ImportError:
    from theme import (
        ACCENT,
        BORDER,
        PLAYHEAD,
        SURFACE,
        TEXT_DIM,
        TEXT_FAINT,
        section_color,
        text_color_on,
        ui_font,
    )

RULER_HEIGHT = 22
SECTION_TOP = RULER_HEIGHT + 4
SECTION_GAP = 2  # pixels between neighbouring section blocks
CHORD_GAP = 6  # space between the section band and the chord lane

# Candidate ruler spacings in seconds; the smallest one that leaves enough
# room for a label wins.
TICK_STEPS = (5, 10, 15, 30, 60, 120, 300)


def time_to_x(seconds, duration, width):
    return (float(seconds) / duration) * width if duration > 0 else 0.0


def format_clock(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


def tick_step(duration, width, min_spacing=64):
    """Ruler label spacing in seconds for the given duration and width."""
    for step in TICK_STEPS:
        if time_to_x(step, duration, width) >= min_spacing:
            return step
    return TICK_STEPS[-1]


def paint_background(painter, rect):
    painter.fillRect(rect, QColor(SURFACE))


def paint_ruler(painter, duration, width):
    """Time labels with major and minor ticks along the top edge."""
    if duration <= 0 or width <= 0:
        return

    step = tick_step(duration, width)
    minor = step / 5
    painter.setFont(ui_font(8))

    # Minor ticks first so major ticks draw over them.
    painter.setPen(QPen(QColor(BORDER), 1))
    t = 0.0
    while t <= duration:
        x = int(time_to_x(t, duration, width))
        painter.drawLine(x, RULER_HEIGHT - 4, x, RULER_HEIGHT)
        t += minor

    for t in range(0, int(duration) + 1, step):
        x = int(time_to_x(t, duration, width))
        painter.setPen(QPen(QColor(TEXT_FAINT), 1))
        painter.drawLine(x, RULER_HEIGHT - 9, x, RULER_HEIGHT)
        painter.setPen(QColor(TEXT_DIM))
        painter.drawText(x + 4, RULER_HEIGHT - 8, format_clock(t))


def _block_rect(start, end, duration, width, top, bottom):
    x1 = time_to_x(start, duration, width)
    x2 = time_to_x(end, duration, width)
    left = x1 + SECTION_GAP / 2
    right = x2 - SECTION_GAP / 2
    return QRectF(left, top, max(1.0, right - left), bottom - top)


def paint_sections(
    painter,
    sections,
    duration,
    width,
    bottom,
    downbeats=(),
    current=-1,
    hovered=-1,
):
    """Rounded, colour-coded section blocks with names and bar lines."""
    if duration <= 0 or not sections or bottom <= SECTION_TOP:
        return

    painter.setRenderHint(painter.RenderHint.Antialiasing, True)
    name_font = ui_font(9.5, QFont.Weight.DemiBold)
    detail_font = ui_font(8)

    for index, section in enumerate(sections):
        start = float(section.get("start", 0))
        end = float(section.get("end", 0))
        if end <= start:
            continue
        rect = _block_rect(start, end, duration, width, SECTION_TOP, bottom)
        base = QColor(section_color(section.get("name", "")))

        fill = QColor(base)
        if current >= 0 and index != current:
            # Sections the playhead is not in recede a little.
            fill = base.darker(135)
        if index == hovered:
            fill = fill.lighter(112)

        path = QPainterPath()
        path.addRoundedRect(rect, 5, 5)
        painter.fillPath(path, fill)

        _paint_bar_lines(painter, downbeats, start, end, duration, width, rect)

        if index == current:
            painter.setPen(QPen(QColor(255, 255, 255, 200), 1.5))
            painter.drawPath(path)

        _paint_section_label(
            painter, section, index, rect, fill, name_font, detail_font
        )

    painter.setRenderHint(painter.RenderHint.Antialiasing, False)


def _paint_bar_lines(painter, downbeats, start, end, duration, width, rect):
    if not downbeats:
        return
    painter.setPen(QPen(QColor(0, 0, 0, 38), 1))
    previous_x = None
    for beat in downbeats:
        if beat <= start or beat >= end:
            continue
        x = int(time_to_x(beat, duration, width))
        if previous_x is not None and x - previous_x < 4:
            continue  # too dense to read at this zoom
        painter.drawLine(x, int(rect.top()) + 26, x, int(rect.bottom()) - 3)
        previous_x = x


def _paint_section_label(painter, section, index, rect, fill, name_font, detail):
    if rect.width() < 18:
        return
    text_rect = rect.adjusted(7, 5, -5, -4)
    name = str(section.get("name", "Section"))
    color = text_color_on(fill)

    painter.setFont(name_font)
    metrics = painter.fontMetrics()
    label = metrics.elidedText(
        name, Qt.TextElideMode.ElideRight, int(text_rect.width())
    )
    if not label or label == "…":
        # Too narrow for a name: fall back to the section number.
        label = str(index + 1)
    painter.setPen(color)
    painter.drawText(
        text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, label
    )

    if rect.height() >= 48 and rect.width() >= 44:
        painter.setFont(detail)
        faded = QColor(color)
        faded.setAlpha(170)
        painter.setPen(faded)
        start = format_clock(section.get("start", 0))
        painter.drawText(
            text_rect.adjusted(0, metrics.height() + 1, 0, 0),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            start,
        )


def paint_playhead(painter, position, duration, width, height):
    """A thin line with a triangular cap in the ruler."""
    if duration <= 0:
        return
    x = time_to_x(position, duration, width)
    painter.setRenderHint(painter.RenderHint.Antialiasing, True)
    shadow = QColor(0, 0, 0, 110)
    painter.setPen(QPen(shadow, 3))
    painter.drawLine(QPointF(x, RULER_HEIGHT), QPointF(x, height))
    painter.setPen(QPen(QColor(PLAYHEAD), 1.5))
    painter.drawLine(QPointF(x, RULER_HEIGHT - 2), QPointF(x, height))

    cap = QPolygonF(
        [
            QPointF(x - 6, RULER_HEIGHT - 10),
            QPointF(x + 6, RULER_HEIGHT - 10),
            QPointF(x, RULER_HEIGHT - 2),
        ]
    )
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(PLAYHEAD))
    painter.drawPolygon(cap)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setRenderHint(painter.RenderHint.Antialiasing, False)


def paint_drag_bubble(painter, text, anchor_x, width):
    """The time readout shown while a boundary is being dragged."""
    if not text:
        return
    painter.setRenderHint(painter.RenderHint.Antialiasing, True)
    painter.setFont(ui_font(9.5, QFont.Weight.DemiBold))
    metrics = painter.fontMetrics()
    bubble_w = metrics.horizontalAdvance(text) + 18
    bubble_h = metrics.height() + 8
    left = max(2.0, min(anchor_x - bubble_w / 2, width - bubble_w - 2))
    rect = QRectF(left, 2, bubble_w, bubble_h)

    path = QPainterPath()
    path.addRoundedRect(rect, bubble_h / 2, bubble_h / 2)
    painter.fillPath(path, QColor(ACCENT))
    painter.setPen(QColor("white"))
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
    painter.setRenderHint(painter.RenderHint.Antialiasing, False)


def paint_placeholder(painter, rect, text):
    """Centred hint text for when there is nothing to draw yet."""
    painter.setFont(ui_font(10))
    painter.setPen(QColor(TEXT_DIM))
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
