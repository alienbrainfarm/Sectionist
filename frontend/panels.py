"""Building blocks of the main window: header, empty state, transport, tables.

The main window wires these together and owns the song state; the widgets
here only know how to look and which signals to raise.
"""

from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap, QPolygonF
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from .theme import BORDER, TEXT_DIM, section_color
except ImportError:
    from theme import BORDER, TEXT_DIM, section_color


def format_clock(seconds):
    seconds = max(0, int(float(seconds or 0)))
    return f"{seconds // 60}:{seconds % 60:02d}"


def make_card(title=None):
    """A rounded panel with an optional small caps title. Returns (card, body)."""
    card = QFrame()
    card.setObjectName("Card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(8)
    if title:
        heading = QLabel(title.upper())
        heading.setObjectName("CardTitle")
        layout.addWidget(heading)
    return card, layout


class HeaderBar(QWidget):
    """Song title and key facts, with the main actions on the right."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 6)
        layout.setSpacing(10)

        text = QVBoxLayout()
        text.setSpacing(2)
        self.title_label = QLabel("Sectionist")
        self.title_label.setObjectName("SongTitle")
        self.meta_label = QLabel("Open a song to find its sections, key and chords")
        self.meta_label.setObjectName("SongMeta")
        text.addWidget(self.title_label)
        text.addWidget(self.meta_label)
        layout.addLayout(text, 1)

        self.open_button = QPushButton("Open…")
        self.open_button.setToolTip("Open an audio file (Ctrl+O)")
        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.setObjectName("Primary")
        self.analyze_button.setToolTip("Run the analysis again (Ctrl+R)")
        self.analyze_button.setEnabled(False)
        for button in (self.open_button, self.analyze_button):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)

    def set_song(self, title, meta):
        self.title_label.setText(title)
        self.title_label.setToolTip(title)
        self.meta_label.setText(meta)


def song_meta(analysis, duration=0.0):
    """One line of facts for the header: key · tempo · length · engine."""
    parts = []
    if analysis:
        if analysis.get("key"):
            parts.append(str(analysis["key"]))
        if analysis.get("tempo"):
            parts.append(f"{float(analysis['tempo']):.0f} BPM")
        duration = analysis.get("duration") or duration
    if duration:
        parts.append(format_clock(duration))
    if analysis and analysis.get("engine"):
        parts.append(str(analysis["engine"]))
    return "  ·  ".join(parts)


class EmptyState(QWidget):
    """What the window shows before a song is loaded: a drop target."""

    open_requested = pyqtSignal()
    load_requested = pyqtSignal()
    recent_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EmptyState")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 8, 18, 18)

        zone = QFrame()
        zone.setObjectName("DropZone")
        zone.setStyleSheet(
            f"QFrame#DropZone {{ border: 2px dashed {BORDER};" " border-radius: 14px; }"
        )
        outer.addWidget(zone)

        layout = QVBoxLayout(zone)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        icon = QLabel("♫")
        icon.setStyleSheet(f"font-size: 44pt; color: {TEXT_DIM};")
        heading = QLabel("Drop a song here")
        heading.setStyleSheet("font-size: 16pt; font-weight: 600;")
        hint = QLabel("MP3, WAV, FLAC, M4A, AIFF, OGG or AAC")
        hint.setObjectName("Dim")
        for label in (icon, heading, hint):
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch()
        open_button = QPushButton("Open audio file…")
        open_button.setObjectName("Primary")
        open_button.clicked.connect(self.open_requested)
        load_button = QPushButton("Load saved song…")
        load_button.clicked.connect(self.load_requested)
        for button in (open_button, load_button):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addSpacing(6)
        layout.addLayout(buttons)

        self.recent_box = QVBoxLayout()
        self.recent_box.setSpacing(0)
        self.recent_box.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(14)
        layout.addLayout(self.recent_box)

    def set_recent(self, paths):
        """List up to five recent files as links under the buttons."""
        while self.recent_box.count():
            widget = self.recent_box.takeAt(0).widget()
            if widget is not None:
                widget.deleteLater()

        existing = [p for p in paths if Path(p).exists()][:5]
        if not existing:
            return
        heading = QLabel("RECENT")
        heading.setObjectName("CardTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recent_box.addWidget(heading)
        for path in existing:
            link = QPushButton(Path(path).name)
            link.setObjectName("Link")
            link.setToolTip(path)
            link.setCursor(Qt.CursorShape.PointingHandCursor)
            link.clicked.connect(lambda _=False, p=path: self.recent_requested.emit(p))
            self.recent_box.addWidget(link, 0, Qt.AlignmentFlag.AlignHCenter)


class TransportBar(QWidget):
    """Play/stop, the position slider, the clock and the current section."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(10)

        # Icons are drawn rather than taken from a font: the media glyphs
        # (U+23F8 and friends) render as colour emoji on Windows.
        self.icons = {kind: transport_icon(kind) for kind in ("play", "pause")}
        self.play_button = QPushButton()
        self.play_button.setObjectName("PlayButton")
        self.play_button.setFixedSize(40, 40)
        self.play_button.setIcon(self.icons["play"])
        self.play_button.setIconSize(QSize(16, 16))
        self.play_button.setToolTip("Play / pause (Space)")

        self.stop_button = QPushButton()
        self.stop_button.setObjectName("RoundButton")
        self.stop_button.setFixedSize(32, 32)
        self.stop_button.setIcon(transport_icon("stop", TEXT_DIM))
        self.stop_button.setIconSize(QSize(10, 10))
        self.stop_button.setToolTip("Stop and return to the start")

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setObjectName("Time")
        self.time_label.setMinimumWidth(110)

        self.position_slider = QSlider(Qt.Orientation.Horizontal)

        self.section_label = QLabel("")
        self.section_label.setObjectName("Chip")
        self.section_label.setVisible(False)

        for button in (self.play_button, self.stop_button):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setEnabled(False)
        self.position_slider.setEnabled(False)

        layout.addWidget(self.play_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.time_label)
        layout.addWidget(self.position_slider, 1)
        layout.addWidget(self.section_label, 0, Qt.AlignmentFlag.AlignVCenter)

    def set_playing(self, playing):
        self.play_button.setIcon(self.icons["pause" if playing else "play"])

    def set_section(self, name):
        """Show which section the playhead is in, coloured to match."""
        if not name:
            self.section_label.setVisible(False)
            return
        color = section_color(name)
        self.section_label.setText(name)
        self.section_label.setStyleSheet(
            f"QLabel#Chip {{ border-color: {color}; color: {color}; }}"
        )
        self.section_label.setVisible(True)


def _swatch(color, size=12):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, size, size, 3, 3)
    painter.end()
    return QIcon(pixmap)


def transport_icon(kind, color="#FFFFFF", size=32):
    """A play triangle, pause bars or stop square, drawn at 2x for sharpness."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    s = size / 32
    if kind == "play":
        points = [QPointF(9 * s, 4 * s), QPointF(28 * s, 16 * s)]
        points.append(QPointF(9 * s, 28 * s))
        painter.drawPolygon(QPolygonF(points))
    elif kind == "pause":
        painter.drawRoundedRect(QRectF(7 * s, 5 * s, 6 * s, 22 * s), 1.5, 1.5)
        painter.drawRoundedRect(QRectF(19 * s, 5 * s, 6 * s, 22 * s), 1.5, 1.5)
    else:
        painter.drawRoundedRect(QRectF(4 * s, 4 * s, 24 * s, 24 * s), 3, 3)
    painter.end()
    return QIcon(pixmap)


def section_chords(chords, start, end, min_overlap=0.25):
    """Chords sounding in [start, end), repeats collapsed.

    A chord that began before the section still counts if it carries on into
    it, so a section that sits on one long chord is not shown as empty.
    """
    sequence = []
    for chord in chords or []:
        chord_start = float(chord.get("start", 0))
        chord_end = float(chord.get("end", chord_start))
        overlap = min(end, chord_end) - max(start, chord_start)
        if overlap >= min(min_overlap, (chord_end - chord_start) / 2):
            name = str(chord.get("name", ""))
            if name and (not sequence or sequence[-1] != name):
                sequence.append(name)
    return sequence


def bar_count(downbeats, start, end):
    return sum(1 for beat in downbeats or [] if start <= float(beat) < end)


class SectionsTable(QTableWidget):
    """One row per section: name, timing, bars, chords and confidence."""

    COLUMNS = ("Section", "Start", "Length", "Bars", "Chords", "Conf.")

    section_activated = pyqtSignal(int)  # row clicked: seek there
    rename_requested = pyqtSignal(int)  # row double-clicked

    def __init__(self, parent=None):
        super().__init__(0, len(self.COLUMNS), parent)
        self.setHorizontalHeaderLabels(self.COLUMNS)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setIconSize(QSize(12, 12))
        self.setWordWrap(False)
        self.verticalHeader().setDefaultSectionSize(30)

        header = self.horizontalHeader()
        header.setHighlightSections(False)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        fixed = QHeaderView.ResizeMode.ResizeToContents
        for column in range(len(self.COLUMNS)):
            header.setSectionResizeMode(column, fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.cellClicked.connect(lambda row, _col: self.section_activated.emit(row))
        self.cellDoubleClicked.connect(
            lambda row, _col: self.rename_requested.emit(row)
        )

    def populate(self, sections, chords=(), downbeats=()):
        self.setRowCount(len(sections))
        for row, section in enumerate(sections):
            name = str(section.get("name", "Unknown"))
            start = float(section.get("start", 0))
            end = float(section.get("end", 0))
            confidence = section.get("confidence")
            sequence = section_chords(chords, start, end)
            bars = bar_count(downbeats, start, end)

            cells = (
                name,
                format_clock(start),
                format_clock(end - start),
                str(bars) if downbeats else "—",
                "  ".join(sequence) or "—",
                "—" if confidence is None else f"{confidence:.0%}",
            )
            for column, value in enumerate(cells):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setIcon(_swatch(section_color(name)))
                if column == 4 and sequence:
                    item.setToolTip(" → ".join(sequence))
                if column in (1, 2, 3, 5):
                    item.setForeground(QColor(TEXT_DIM))
                self.setItem(row, column, item)

    def cell_text(self, row, column):
        item = self.item(row, column)
        return item.text() if item else ""

    def toPlainText(self):
        """Every row as tab-separated text, for tests and copy-paste."""
        lines = []
        for row in range(self.rowCount()):
            cells = [self.cell_text(row, c) for c in range(self.columnCount())]
            lines.append("\t".join(cells))
        return "\n".join(lines)
