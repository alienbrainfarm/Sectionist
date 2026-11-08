"""Colours, fonts and the application stylesheet.

Everything visual that more than one module needs lives here, so the timeline,
the chord lane and the panels agree on one palette.
"""

from PyQt6.QtGui import QColor, QFont, QPalette

# --- base palette ----------------------------------------------------------

BG = "#15171C"  # window background
SURFACE = "#1C1F26"  # cards and panels
SURFACE_ALT = "#242833"  # inputs, table headers, lanes
SURFACE_HOVER = "#2C3140"
BORDER = "#2F3441"
TEXT = "#E6E8EE"
TEXT_DIM = "#9AA1B0"
TEXT_FAINT = "#6B7280"
ACCENT = "#6E8BFF"
ACCENT_HOVER = "#8AA1FF"
ACCENT_PRESSED = "#5873E6"
PLAYHEAD = "#FFFFFF"

# --- section colours -------------------------------------------------------

# Mid-saturation colours that stay distinct on the dark background. Order
# matters for partial matching: "pre-chorus" must be tried before "chorus".
SECTION_COLORS = {
    "pre-chorus": "#E3A857",  # amber
    "post-chorus": "#D987B9",  # pink
    "intro": "#5F8FE8",  # blue
    "verse": "#4FB07E",  # green
    "chorus": "#E8686C",  # coral
    "bridge": "#9C7FE6",  # violet
    "outro": "#4DB3C2",  # teal
    "instrumental": "#6CC3A9",  # sea green
    "solo": "#EE8A5C",  # orange
    "breakdown": "#7D86E0",  # indigo
    "interlude": "#CDBB5A",  # olive gold
}
DEFAULT_SECTION_COLOR = "#7D8594"


def section_color(name):
    """Colour for a section, matched by type ("Verse 2" is a verse)."""
    text = str(name or "").lower().strip()
    if text in SECTION_COLORS:
        return SECTION_COLORS[text]
    # "prechorus" and "pre chorus" are common spellings of the same thing.
    normalized = text.replace(" ", "-")
    if normalized.startswith("prechorus"):
        normalized = "pre-" + normalized[3:]
    for kind, color in SECTION_COLORS.items():
        if kind in normalized:
            return color
    return DEFAULT_SECTION_COLOR


def text_color_on(background):
    """Near-black or near-white, whichever reads better on ``background``."""
    color = QColor(background)
    luminance = 0.2126 * color.redF() + 0.7152 * color.greenF() + 0.0722 * color.blueF()
    return QColor("#111318") if luminance > 0.42 else QColor("#F7F8FA")


def ui_font(point_size=10, weight=QFont.Weight.Normal):
    """The interface font at a given size and weight."""
    font = QFont()
    font.setPointSizeF(point_size)
    font.setWeight(weight)
    return font


# --- application-wide styling ---------------------------------------------

STYLESHEET = f"""
QMainWindow, QWidget#Workspace, QWidget#EmptyState {{
    background: {BG};
}}
QWidget {{
    color: {TEXT};
}}
QToolTip {{
    background: {SURFACE_ALT};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 4px 6px;
}}

QMenuBar {{
    background: {BG};
    border-bottom: 1px solid {BORDER};
    padding: 2px 4px;
}}
QMenuBar::item {{
    padding: 4px 10px;
    border-radius: 4px;
    background: transparent;
}}
QMenuBar::item:selected {{
    background: {SURFACE_HOVER};
}}
QMenu {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px 6px 20px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background: {ACCENT};
    color: white;
}}
QMenu::item:disabled {{
    color: {TEXT_FAINT};
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 4px 8px;
}}

QFrame#Card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QLabel#CardTitle {{
    color: {TEXT_DIM};
    font-size: 8.5pt;
    font-weight: 600;
}}
QLabel#SongTitle {{
    font-size: 15pt;
    font-weight: 600;
}}
QLabel#SongMeta, QLabel#Dim {{
    color: {TEXT_DIM};
}}
QLabel#Chip {{
    background: {SURFACE_ALT};
    border: 1px solid {BORDER};
    border-radius: 11px;
    padding: 2px 10px;
    color: {TEXT};
}}
QLabel#Time {{
    font-family: "Cascadia Mono", "Consolas", "Menlo", monospace;
    font-size: 11pt;
    color: {TEXT};
}}

QPushButton {{
    background: {SURFACE_ALT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 14px;
    color: {TEXT};
}}
QPushButton:hover {{
    background: {SURFACE_HOVER};
}}
QPushButton:pressed {{
    background: {BORDER};
}}
QPushButton:disabled {{
    color: {TEXT_FAINT};
    background: {SURFACE};
}}
QPushButton#Primary {{
    background: {ACCENT};
    border: 1px solid {ACCENT};
    color: white;
    font-weight: 600;
}}
QPushButton#Primary:hover {{
    background: {ACCENT_HOVER};
}}
QPushButton#Primary:pressed {{
    background: {ACCENT_PRESSED};
}}
QPushButton#Primary:disabled {{
    background: {SURFACE_ALT};
    border-color: {BORDER};
    color: {TEXT_FAINT};
}}
QPushButton#PlayButton {{
    background: {ACCENT};
    border: none;
    border-radius: 20px;
    color: white;
    font-size: 13pt;
    padding: 0;
}}
QPushButton#PlayButton:hover {{
    background: {ACCENT_HOVER};
}}
QPushButton#PlayButton:disabled {{
    background: {SURFACE_ALT};
    color: {TEXT_FAINT};
}}
QPushButton#RoundButton {{
    border-radius: 16px;
    padding: 0;
    font-size: 10pt;
}}
QPushButton#Link {{
    background: transparent;
    border: none;
    color: {ACCENT_HOVER};
    padding: 2px 4px;
    text-align: left;
}}
QPushButton#Link:hover {{
    color: white;
    text-decoration: underline;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {SURFACE_HOVER};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: white;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::handle:horizontal:disabled {{
    background: {TEXT_FAINT};
}}

QTableWidget, QTextEdit {{
    background: {SURFACE};
    border: none;
    selection-background-color: {SURFACE_HOVER};
    selection-color: {TEXT};
    gridline-color: transparent;
}}
QTableWidget::item {{
    padding: 4px 6px;
    border-bottom: 1px solid {BORDER};
}}
QHeaderView::section {{
    background: {SURFACE};
    color: {TEXT_DIM};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 6px;
    font-weight: 600;
}}
QTableCornerButton::section {{
    background: {SURFACE};
    border: none;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {SURFACE_HOVER};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_FAINT};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
    width: 0;
}}
QScrollBar::add-page, QScrollBar::sub-page {{
    background: transparent;
}}

QSplitter::handle {{
    background: transparent;
}}

QStatusBar {{
    background: {BG};
    border-top: 1px solid {BORDER};
    color: {TEXT_DIM};
}}
QStatusBar QLabel {{
    color: {TEXT_DIM};
    padding: 2px 10px;
}}
QStatusBar::item {{
    border: none;
}}
QProgressBar {{
    background: {SURFACE_ALT};
    border: none;
    border-radius: 3px;
    max-height: 6px;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 3px;
}}

QDockWidget {{
    color: {TEXT_DIM};
    font-weight: 600;
}}
QDockWidget::title {{
    background: {BG};
    padding: 8px 10px;
}}

QInputDialog, QMessageBox, QFileDialog {{
    background: {SURFACE};
}}
QLineEdit {{
    background: {SURFACE_ALT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}
"""


def apply_theme(app):
    """Give the whole application the Sectionist look."""
    app.setStyle("Fusion")

    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: BG,
        QPalette.ColorRole.WindowText: TEXT,
        QPalette.ColorRole.Base: SURFACE,
        QPalette.ColorRole.AlternateBase: SURFACE_ALT,
        QPalette.ColorRole.Text: TEXT,
        QPalette.ColorRole.Button: SURFACE_ALT,
        QPalette.ColorRole.ButtonText: TEXT,
        QPalette.ColorRole.Highlight: ACCENT,
        QPalette.ColorRole.HighlightedText: "#FFFFFF",
        QPalette.ColorRole.ToolTipBase: SURFACE_ALT,
        QPalette.ColorRole.ToolTipText: TEXT,
        QPalette.ColorRole.PlaceholderText: TEXT_FAINT,
        QPalette.ColorRole.Link: ACCENT_HOVER,
    }
    for role, color in roles.items():
        palette.setColor(role, QColor(color))
    for role in (
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
        QPalette.ColorRole.WindowText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(TEXT_FAINT))
    app.setPalette(palette)

    font = app.font()
    font.setPointSizeF(max(font.pointSizeF(), 9.5))
    app.setFont(font)
    app.setStyleSheet(STYLESHEET)
