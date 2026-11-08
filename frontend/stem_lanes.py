"""Stem lanes: one waveform per stem under the timeline, with mute and solo.

The lanes share the timeline's time axis. Their controls sit in a gutter on the
left, and the timeline gets a matching gutter (with "Sections" and "Chords"
labels) while stems are shown, so a beat in a waveform sits exactly under the
same moment in the section and chord lanes.
"""

from PyQt6.QtCore import QLineF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

try:
    from . import timeline_paint as paint
    from .chord_track import CHORD_LANE_HEIGHT
    from .theme import BORDER, PLAYHEAD, SURFACE, TEXT, TEXT_DIM, ui_font
except ImportError:
    import timeline_paint as paint
    from chord_track import CHORD_LANE_HEIGHT
    from theme import BORDER, PLAYHEAD, SURFACE, TEXT, TEXT_DIM, ui_font

GUTTER = 132
LANE_HEIGHT = 46

STEM_COLORS = {
    "vocals": "#ED93B1",
    "drums": "#FAC775",
    "bass": "#5DCAA5",
    "guitar": "#F0997B",
    "piano": "#85B7EB",
    "other": "#AFA9EC",
}
DEFAULT_STEM_COLOR = "#B4B2A9"

STYLE = """
QPushButton#Mute, QPushButton#Solo {
    min-width: 24px; max-width: 24px; min-height: 22px; max-height: 22px;
    padding: 0; font-size: 8pt; font-weight: 600;
}
QPushButton#Mute:checked {
    background: #E24B4A; border-color: #E24B4A; color: #FFFFFF;
}
QPushButton#Solo:checked {
    background: #EF9F27; border-color: #EF9F27; color: #111318;
}
QPushButton#Small { padding: 3px 10px; }
"""


def stem_color(name):
    return QColor(STEM_COLORS.get(name, DEFAULT_STEM_COLOR))


def audible_stems(names, muted, soloed):
    """Which stems are heard: soloed ones if any are, minus the muted ones."""
    heard = [name for name in names if not soloed or name in soloed]
    return [name for name in heard if name not in muted]


def column_peaks(peaks, width):
    """Resample peaks to one value per pixel column."""
    import numpy as np

    if width <= 0 or len(peaks) == 0:
        return np.zeros(max(width, 0), dtype=np.float32)
    edges = np.linspace(0, len(peaks), width + 1).astype(np.int64)
    edges = np.minimum(edges, len(peaks) - 1)
    return np.maximum.reduceat(peaks, edges[:-1])


class WaveformView(QWidget):
    """One stem's waveform. Clicking seeks there."""

    seek_requested = pyqtSignal(float)

    def __init__(self, name, peaks, parent=None):
        super().__init__(parent)
        self.name = name
        self.peaks = peaks
        self.color = stem_color(name)
        self.audible = True
        self.duration = 0.0
        self.position = 0.0
        self.boundaries = []
        self.cycle = None  # CycleRegion shaded over the waveform
        self._cache = None  # (key, pixmap); the playhead is drawn on top
        self.setMinimumHeight(LANE_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def invalidate(self):
        self._cache = None
        self.update()

    def _waveform(self):
        key = (self.width(), self.height(), self.audible, self.duration)
        if self._cache and self._cache[0] == key:
            return self._cache[1]
        ratio = self.devicePixelRatioF()
        pixmap = QPixmap(int(self.width() * ratio), int(self.height() * ratio))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(SURFACE))
        painter.drawRoundedRect(QRectF(0, 0, width, height), 6, 6)

        painter.setPen(QColor(BORDER))
        for seconds in self.boundaries:
            x = paint.time_to_x(seconds, self.duration, width)
            painter.drawLine(QLineF(x, 0, x, height))

        color = QColor(self.color)
        color.setAlphaF(0.9 if self.audible else 0.18)
        painter.setPen(color)
        middle, reach = height / 2, height * 0.45
        lines = [
            QLineF(x + 0.5, middle - value * reach, x + 0.5, middle + value * reach)
            for x, value in enumerate(column_peaks(self.peaks, width))
            if value > 0.01
        ]
        painter.drawLines(lines)

        if not self.audible:
            painter.setPen(QColor(TEXT_DIM))
            painter.setFont(ui_font(8))
            painter.drawText(QRectF(8, 2, width, 16), "silent")
        painter.end()
        self._cache = (key, pixmap)
        return pixmap

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._waveform())
        if self.cycle is not None and self.duration > 0:
            left = paint.time_to_x(self.cycle.start, self.duration, self.width())
            right = paint.time_to_x(self.cycle.end, self.duration, self.width())
            painter.fillRect(
                QRectF(left, 0, right - left, self.height()), QColor(245, 197, 66, 28)
            )
        if self.duration > 0:
            x = paint.time_to_x(self.position, self.duration, self.width())
            painter.setPen(QColor(PLAYHEAD))
            painter.drawLine(QLineF(x, 0, x, self.height()))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.duration > 0:
            fraction = min(max(event.position().x() / max(self.width(), 1), 0.0), 1.0)
            self.seek_requested.emit(fraction * self.duration)


class StemRow(QWidget):
    """Gutter controls plus the waveform for one stem."""

    def __init__(self, name, peaks, parent=None):
        super().__init__(parent)
        self.name = name
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        gutter = QWidget()
        gutter.setFixedWidth(GUTTER)
        controls = QHBoxLayout(gutter)
        controls.setContentsMargins(0, 0, 10, 0)
        controls.setSpacing(6)
        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background: {stem_color(name).name()}; border-radius: 4px;")
        label = QLabel(name.capitalize())
        label.setStyleSheet(f"color: {TEXT};")
        self.mute_button = self._toggle("M", "Mute", f"Mute {name} (Shift: solo)")
        self.solo_button = self._toggle("S", "Solo", f"Solo {name}")
        controls.addWidget(dot)
        controls.addWidget(label, 1)
        controls.addWidget(self.mute_button)
        controls.addWidget(self.solo_button)

        self.waveform = WaveformView(name, peaks)
        layout.addWidget(gutter)
        layout.addWidget(self.waveform, 1)

    def _toggle(self, text, kind, tip):
        button = QPushButton(text)
        button.setObjectName(kind)
        button.setCheckable(True)
        button.setToolTip(tip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button


class StemLanes(QWidget):
    """The stems card body: a header line, then one StemRow per stem."""

    mix_changed = pyqtSignal(list)  # names of the stems that should be heard
    seek_requested = pyqtSignal(float)
    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLE)
        self.rows = []
        self.muted, self.soloed = set(), set()
        self.duration = 0.0
        self.boundaries = []
        self.cycle = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 0)
        layout.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel("STEMS")
        title.setObjectName("CardTitle")
        self.model_label = QLabel("")
        self.model_label.setObjectName("Dim")
        self.reset_button = QPushButton("Unmute all")
        self.close_button = QPushButton("Original mix")
        self.close_button.setToolTip("Hide the stems and play the original file")
        for button in (self.reset_button, self.close_button):
            button.setObjectName("Small")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_button.clicked.connect(self.reset)
        self.close_button.clicked.connect(self.close_requested)
        header.addWidget(title)
        header.addWidget(self.model_label)
        header.addStretch(1)
        header.addWidget(self.reset_button)
        header.addWidget(self.close_button)
        layout.addLayout(header)

        self.message = QLabel("")
        self.message.setObjectName("Dim")
        self.message.setContentsMargins(GUTTER, 4, 0, 4)
        layout.addWidget(self.message)

        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(6)
        layout.addLayout(self.rows_layout)
        self.setVisible(False)

    # --- content -------------------------------------------------------------

    def show_message(self, text):
        """Show progress or an error in place of the lanes."""
        self.clear_rows()
        self.model_label.setText("")
        self.message.setText(text)
        self.message.setVisible(True)
        self.reset_button.setVisible(False)
        self.setVisible(True)

    def set_stems(self, stem_set, duration):
        self.clear_rows()
        self.message.setVisible(False)
        self.reset_button.setVisible(True)
        self.model_label.setText(stem_set.model)
        self.duration = duration
        for name in stem_set.names:
            row = StemRow(name, stem_set.peaks.get(name, ()))
            row.mute_button.clicked.connect(lambda _=False, n=name: self.toggle_mute(n))
            row.solo_button.clicked.connect(lambda _=False, n=name: self.toggle_solo(n))
            row.waveform.seek_requested.connect(self.seek_requested)
            row.waveform.duration = duration
            row.waveform.boundaries = self.boundaries
            row.waveform.cycle = self.cycle
            self.rows_layout.addWidget(row)
            self.rows.append(row)
        self.setVisible(True)
        self.refresh()

    def clear_rows(self):
        for row in self.rows:
            row.setParent(None)
            row.deleteLater()
        self.rows = []
        self.muted, self.soloed = set(), set()

    def clear(self):
        self.clear_rows()
        self.setVisible(False)

    @property
    def has_stems(self):
        return bool(self.rows)

    def set_sections(self, sections):
        self.boundaries = [float(s.get("start", 0)) for s in sections[1:]]
        for row in self.rows:
            row.waveform.boundaries = self.boundaries
            row.waveform.invalidate()

    def set_cycle(self, region):
        """Shade the looping region (a CycleRegion, or None) in every lane."""
        self.cycle = region
        for row in self.rows:
            row.waveform.cycle = region
            row.waveform.update()

    def set_position(self, position):
        for row in self.rows:
            row.waveform.position = position
            row.waveform.update()

    # --- mute and solo -------------------------------------------------------

    def names(self):
        return [row.name for row in self.rows]

    def toggle_mute(self, name):
        if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.soloed = {name}
            self.muted.discard(name)
        else:
            self.muted ^= {name}
        self.refresh()

    def toggle_solo(self, name):
        self.soloed ^= {name}
        self.refresh()

    def reset(self):
        self.muted, self.soloed = set(), set()
        self.refresh()

    def audible(self):
        return audible_stems(self.names(), self.muted, self.soloed)

    def refresh(self):
        heard = set(self.audible())
        for row in self.rows:
            row.mute_button.setChecked(row.name in self.muted)
            row.solo_button.setChecked(row.name in self.soloed)
            if row.waveform.audible != (row.name in heard):
                row.waveform.audible = row.name in heard
                row.waveform.invalidate()
        self.reset_button.setEnabled(bool(self.muted or self.soloed))
        self.mix_changed.emit(self.audible())


class TimelineGutter(QWidget):
    """Lane names to the left of the timeline, matching the stem gutter."""

    def __init__(self, timeline, parent=None):
        super().__init__(parent)
        self.timeline = timeline
        self.setFixedWidth(GUTTER)
        self.setVisible(False)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setPen(QColor(TEXT_DIM))
        painter.setFont(ui_font(9))
        height = self.height()
        has_chords = bool(self.timeline.chords)
        bottom = height - CHORD_LANE_HEIGHT - paint.CHORD_GAP if has_chords else height
        align = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        band = QRectF(0, paint.SECTION_TOP, GUTTER, bottom - paint.SECTION_TOP)
        painter.drawText(band, align, "Sections")
        if has_chords:
            lane = QRectF(0, height - CHORD_LANE_HEIGHT, GUTTER, CHORD_LANE_HEIGHT)
            painter.drawText(lane, align, "Chords")
