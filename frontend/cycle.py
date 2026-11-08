"""Cycle (loop) region, in the manner of Logic's cycle area.

- Drag in the timeline's ruler to create a region; it snaps to bar lines
  (hold Alt to place it freely). Drag its edges to resize, its middle to
  move. A click on it turns cycling on and off.
- C toggles cycling (looping the current section if there is no region yet);
  right-click a section and choose "Loop This Section".
- Playback that reaches the end of the region jumps back to its start.
  Starting after the region plays on normally, as in Logic.

The stem player loops sample-accurately in its mixer; VLC is sent back with
a seek on the playback tick, so it can overshoot by a few tens of ms.
"""

from dataclasses import dataclass

from PyQt6.QtCore import QObject, QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QAction, QColor, QIcon, QKeySequence, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QPushButton

try:
    from .theme import TEXT
except ImportError:
    from theme import TEXT

CYCLE_ON = QColor("#F5C542")  # Logic's cycle area is yellow
CYCLE_OFF = QColor("#5B6070")
MIN_LENGTH = 0.2  # seconds
# VLC is polled every 50 ms; jumping half a tick early lands closer to the end.
EARLY = 0.025
MAX_TICK = 0.5  # seconds a playback tick can advance; more is a seek
SNAP_PIXELS = 12
EDGE_PIXELS = 5


@dataclass
class CycleRegion:
    start: float
    end: float
    enabled: bool = True

    def contains(self, seconds):
        return self.start <= seconds < self.end


def snap(seconds, downbeats, duration, width, free=False):
    """The nearest bar line within SNAP_PIXELS, else the time itself."""
    seconds = min(max(0.0, seconds), duration)
    if free or not downbeats or duration <= 0 or width <= 0:
        return seconds
    nearest = min(downbeats, key=lambda beat: abs(beat - seconds))
    if abs(nearest - seconds) / duration * width <= SNAP_PIXELS:
        return float(nearest)
    return seconds


def hit_test(region, x, duration, width):
    """'start', 'end', 'inside' or None for a ruler x coordinate."""
    if region is None or duration <= 0:
        return None
    left = region.start / duration * width
    right = region.end / duration * width
    if abs(x - left) <= EDGE_PIXELS:
        return "start"
    if abs(x - right) <= EDGE_PIXELS:
        return "end"
    if left < x < right:
        return "inside"
    return None


class CycleDrag:
    """Turns ruler mouse presses, moves and releases into a region."""

    def __init__(self):
        self.mode = None  # 'new', 'start', 'end', 'move'
        self.anchor = 0.0
        self.original = None
        self.moved = False

    @property
    def active(self):
        return self.mode is not None

    def press(self, region, seconds, x, duration, width):
        part = hit_test(region, x, duration, width)
        self.mode = {"start": "start", "end": "end", "inside": "move"}.get(part, "new")
        self.anchor = seconds
        self.original = region
        self.moved = False

    def move(self, seconds, downbeats, duration, width, free=False):
        """The region as it should look now, or None while still a click."""
        if abs(seconds - self.anchor) / max(duration, 1e-9) * width >= 3:
            self.moved = True
        if not self.moved:
            return self.original
        region = self.original

        def at(t):
            return snap(t, downbeats, duration, width, free)

        if self.mode == "new":
            a, b = sorted((at(self.anchor), at(seconds)))
            return CycleRegion(a, b) if b - a >= MIN_LENGTH else self.original
        if self.mode == "start":
            start = min(at(seconds), region.end - MIN_LENGTH)
            return CycleRegion(start, region.end, region.enabled)
        if self.mode == "end":
            end = max(at(seconds), region.start + MIN_LENGTH)
            return CycleRegion(region.start, end, region.enabled)
        length = region.end - region.start
        start = at(region.start + seconds - self.anchor)
        start = min(max(0.0, start), duration - length)
        return CycleRegion(start, start + length, region.enabled)

    def release(self):
        """True when the gesture was a click rather than a drag."""
        clicked = not self.moved
        self.mode = None
        return clicked


def paint_cycle(painter, region, duration, width, ruler_height, height):
    """The yellow bar in the ruler and a light wash over the lanes below."""
    if region is None or duration <= 0:
        return
    left = region.start / duration * width
    right = region.end / duration * width
    color = QColor(CYCLE_ON if region.enabled else CYCLE_OFF)
    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawRoundedRect(QRectF(left, 2, right - left, ruler_height - 6), 3, 3)
    if region.enabled:
        wash = QColor(color)
        wash.setAlpha(28)
        painter.fillRect(QRectF(left, ruler_height, right - left, height), wash)
        painter.setPen(QPen(QColor(color), 1))
        painter.drawLine(QPointF(left, ruler_height), QPointF(left, height))
        painter.drawLine(QPointF(right, ruler_height), QPointF(right, height))
    painter.restore()


def cycle_icon(color=TEXT, size=32):
    """Two arrows chasing each other round a loop."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), size * 0.09)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    box = QRectF(size * 0.2, size * 0.28, size * 0.6, size * 0.44)
    painter.drawArc(box, 30 * 16, 150 * 16)
    painter.drawArc(box, 210 * 16, 150 * 16)
    tip = size * 0.1
    for x, y, direction in (
        (box.right(), box.center().y() - 2, 1),
        (box.left(), box.center().y() + 2, -1),
    ):
        painter.drawLine(QPointF(x, y), QPointF(x - tip, y - direction * tip))
        painter.drawLine(QPointF(x, y), QPointF(x + tip, y - direction * tip))
    painter.end()
    return QIcon(pixmap)


class CycleController(QObject):
    """Owns the region and makes playback loop inside it."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.region = None
        self.last_position = 0.0

        self.button = QPushButton()
        self.button.setObjectName("RoundButton")
        self.button.setCheckable(True)
        self.button.setFixedSize(32, 32)
        self.button.setIcon(cycle_icon())
        self.button.setIconSize(QSize(18, 18))
        self.button.setToolTip("Cycle (C): loop the yellow region in the ruler")
        self.button.setStyleSheet(
            f"QPushButton:checked {{ background: {CYCLE_ON.name()};"
            f" border-color: {CYCLE_ON.name()}; }}"
        )
        self.button.clicked.connect(self.toggle)
        transport = window.transport.layout()
        transport.insertWidget(transport.indexOf(window.stop_button) + 1, self.button)

        self.action = QAction("Cycle", window)
        self.action.setCheckable(True)
        self.action.setShortcut(QKeySequence("C"))
        self.action.triggered.connect(self.toggle)
        window.playback_menu.addSeparator()
        window.playback_menu.addAction(self.action)
        self.loop_section_action = QAction("Loop Current Section", window)
        self.loop_section_action.setShortcut(QKeySequence("Shift+C"))
        self.loop_section_action.triggered.connect(self.loop_current_section)
        window.playback_menu.addAction(self.loop_section_action)

        window.timeline.cycle_changed.connect(self.set_region)
        window.timeline.position_changed.connect(self.on_position)

    # --- region ---------------------------------------------------------------

    def set_region(self, region, snap=True):
        """Show and apply a region.

        Turning a loop on (or making a new one) moves the playhead to its
        start, so practice begins at the top of the loop; so does editing an
        active loop so that the playhead falls outside it. ``snap=False``
        restores a saved region without moving anything.
        """
        was_on = bool(self.region and self.region.enabled)
        self.region = region
        enabled = bool(region and region.enabled)
        for widget in (self.button, self.action):
            widget.blockSignals(True)
            widget.setChecked(enabled)
            widget.blockSignals(False)
        self.window.timeline.cycle = region
        self.window.timeline.update()
        self.window.stem_lanes.set_cycle(region if enabled else None)
        stems = self.window.stems.stem_player
        stems.set_loop((region.start, region.end) if enabled else None)
        self.last_position = self.window.timeline.current_position
        outside = enabled and not region.contains(self.last_position)
        if snap and enabled and (not was_on or outside):
            self.window.seek_to_position(region.start)
            self.last_position = region.start

    def toggle(self):
        if self.region is None:
            self.loop_current_section()
            return
        self.set_region(
            CycleRegion(self.region.start, self.region.end, not self.region.enabled)
        )

    def loop_current_section(self):
        timeline = self.window.timeline
        index = timeline.current_section()
        if index < 0 and timeline.sections:
            index = 0
        if index < 0:
            self.set_region(self.region)  # nothing to loop: undo the check
            return
        section = timeline.sections[index]
        self.set_region(CycleRegion(float(section["start"]), float(section["end"])))

    def clear(self):
        self.set_region(None)

    def saved(self):
        """The region as stored in a saved song's analysis.json, or None."""
        region = self.region
        if region is None:
            return None
        return {"start": region.start, "end": region.end, "enabled": region.enabled}

    def restore(self, saved):
        """Bring back a region from a saved song (ignores anything malformed)."""
        try:
            region = CycleRegion(
                float(saved["start"]), float(saved["end"]), bool(saved["enabled"])
            )
        except (TypeError, KeyError, ValueError):
            region = None
        self.set_region(region, snap=False)

    # --- playback -------------------------------------------------------------

    def on_position(self, position):
        """Jump back to the start when playback crosses the region's end."""
        previous, self.last_position = self.last_position, position
        region, player = self.region, self.window.audio_player
        if region is None or not region.enabled or not player.is_playing:
            return
        if player is self.window.stems.stem_player:
            return  # the mixer loops on its own, sample-accurately
        # Playback moves ~50 ms per tick; a bigger jump is the user seeking,
        # possibly past the region, and must not be pulled back.
        playing_on = 0 <= position - previous < MAX_TICK
        # Usually caught half a tick early; a start inside that last half
        # tick is caught when it passes the end itself.
        crossed = previous < region.end - EARLY <= position or (
            previous < region.end <= position
        )
        if playing_on and crossed:
            self.last_position = region.start
            self.window.seek_to_position(region.start)
