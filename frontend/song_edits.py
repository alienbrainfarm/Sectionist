"""Locks for sections, chords and lyrics, and editing the lyrics.

Once a part is right, lock it: the timeline stops accepting edits to it, the
lyrics become read-only, and a fresh analysis leaves it alone, so practice
material cannot be changed by accident. Locks are saved with the song.
"""

from PyQt6.QtCore import QObject, QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

try:
    from .theme import ACCENT, TEXT_DIM
except ImportError:
    from theme import ACCENT, TEXT_DIM

KINDS = ("sections", "chords", "lyrics")
LABELS = {"sections": "Sections", "chords": "Chords", "lyrics": "Lyrics"}
# What a lock keeps from the previous analysis when the song is analysed again.
LOCKED_FIELDS = {
    "sections": ("sections",),
    "chords": ("chords",),
    "lyrics": ("lyrics", "lyrics_text", "lyrics_available"),
}


def padlock_icon(locked, size=32):
    """A padlock, closed in the accent colour when locked, open and dim if not."""
    color = QColor(ACCENT if locked else TEXT_DIM)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    body = QRectF(size * 0.22, size * 0.45, size * 0.56, size * 0.42)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawRoundedRect(body, size * 0.06, size * 0.06)
    pen = QPen(color, size * 0.09)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    shackle = QRectF(size * 0.32, size * 0.14, size * 0.36, size * 0.5)
    if locked:
        painter.drawArc(shackle, 0, 180 * 16)
        painter.drawLine(
            QPointF(shackle.left(), shackle.center().y()),
            QPointF(shackle.left(), body.top()),
        )
    else:
        shackle.translate(size * 0.16, -size * 0.06)
        painter.drawArc(shackle, 0, 180 * 16)
    painter.drawLine(
        QPointF(shackle.right(), shackle.center().y()),
        QPointF(shackle.right(), body.top() - (0 if locked else size * 0.1)),
    )
    painter.end()
    return QIcon(pixmap)


def lock_button(kind, parent=None):
    button = QToolButton(parent)
    button.setCheckable(True)
    button.setAutoRaise(True)
    button.setIcon(padlock_icon(False))
    button.setIconSize(QSize(16, 16))
    button.setToolTip(f"Lock {LABELS[kind].lower()} so they cannot be changed")
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


class LockController(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.locked = dict.fromkeys(KINDS, False)

        menu = QMenu("&Edit", window)
        window.menuBar().insertMenu(window.playback_menu.menuAction(), menu)
        self.actions = {}
        for kind in KINDS:
            action = menu.addAction(f"Lock {LABELS[kind]}")
            action.setCheckable(True)
            action.toggled.connect(lambda on, k=kind: self.set_locked(k, on))
            self.actions[kind] = action

        self.buttons = {
            "sections": window.timeline_gutter.sections_lock,
            "chords": window.timeline_gutter.chords_lock,
            "lyrics": self._lyrics_header(),
        }
        for kind, button in self.buttons.items():
            button.toggled.connect(lambda on, k=kind: self.set_locked(k, on))

        text = window.lyrics_text
        text.setReadOnly(False)
        text.setPlaceholderText("Lyrics appear here after an analysis; edit freely.")
        text.textChanged.connect(self.lyrics_edited)

    def _lyrics_header(self):
        """Put a lock and a hint above the lyrics text."""
        dock, text = self.window.lyrics_dock, self.window.lyrics_text
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = QHBoxLayout()
        header.setContentsMargins(12, 6, 8, 0)
        hint = QLabel("Edit freely. [Section] lines place lyrics on the gig sheet.")
        hint.setObjectName("Dim")
        hint.setWordWrap(True)
        button = lock_button("lyrics")
        header.addWidget(button, 0, Qt.AlignmentFlag.AlignTop)
        header.addWidget(hint, 1)
        layout.addLayout(header)
        layout.addWidget(text, 1)
        dock.setWidget(container)
        return button

    # --- state ----------------------------------------------------------------

    def set_locked(self, kind, on):
        self.locked[kind] = bool(on)
        for widget in (self.actions[kind], self.buttons[kind]):
            widget.blockSignals(True)
            widget.setChecked(self.locked[kind])
            widget.blockSignals(False)
        button = self.buttons[kind]
        button.setIcon(padlock_icon(self.locked[kind]))
        verb = "locked" if self.locked[kind] else "unlocked"
        button.setToolTip(f"{LABELS[kind]} {verb}: click to toggle")
        timeline = self.window.timeline
        timeline.sections_locked = self.locked["sections"]
        timeline.chords_locked = self.locked["chords"]
        timeline.update()
        self.window.lyrics_text.setReadOnly(self.locked["lyrics"])

    def reset(self):
        for kind in KINDS:
            self.set_locked(kind, False)

    def saved(self):
        return dict(self.locked)

    def restore(self, saved):
        saved = saved if isinstance(saved, dict) else {}
        for kind in KINDS:
            self.set_locked(kind, bool(saved.get(kind)))

    def keep_locked(self, results):
        """New analysis results with every locked part carried over."""
        previous = (self.window.analysis_results or {}).get("analysis")
        if not previous or not any(self.locked.values()):
            return results
        analysis = dict(results.get("analysis", {}))
        for kind, fields in LOCKED_FIELDS.items():
            if self.locked[kind]:
                for field in fields:
                    if field in previous:
                        analysis[field] = previous[field]
                    else:
                        analysis.pop(field, None)
        return dict(results, analysis=analysis)

    def lyrics_edited(self):
        """Keep what the user typed (not what the app filled in)."""
        text = self.window.lyrics_text
        results = self.window.analysis_results
        if results is None or not text.document().isModified():
            return
        results.setdefault("analysis", {})["lyrics_text"] = text.toPlainText()
