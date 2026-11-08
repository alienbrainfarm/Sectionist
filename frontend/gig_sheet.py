"""An A4 gig sheet: the song's structure, chords per bar and lyrics.

One block per section, in order: its name and length, a bar-by-bar chord grid
("| D | A | Bm | G |", with % for a bar that repeats the one before) and the
lyrics sung over it. Print it, or save it straight to PDF.
"""

from html import escape
from pathlib import Path

from PyQt6.QtCore import QMarginsF, QObject, Qt
from PyQt6.QtGui import (
    QAction,
    QKeySequence,
    QPageLayout,
    QPageSize,
    QPdfWriter,
    QTextDocument,
)
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox

try:
    from .lyrics_view import lyrics_per_section, section_name
    from .panels import bar_count, section_chords
    from .theme import section_color, text_color_on
except ImportError:
    from lyrics_view import lyrics_per_section, section_name
    from panels import bar_count, section_chords
    from theme import section_color, text_color_on

BARS_PER_LINE = 4
MARGIN_MM = 12


def chord_at(chords, seconds):
    for chord in chords:
        if float(chord.get("start", 0)) <= seconds < float(chord.get("end", 0)):
            return str(chord.get("name", ""))
    return ""


def bar_chords(chords, downbeats, start, end):
    """Chord names for each bar of a section: one, or two if it changes mid-bar.

    Bars are the downbeats inside the section (edges snapped as bar_count
    does). A change counts only from about a beat into the bar, so a chord
    that is late by a few milliseconds does not split the bar.
    """
    beats = sorted(float(beat) for beat in downbeats or [])
    gaps = sorted(b - a for a, b in zip(beats, beats[1:]))
    slack = gaps[len(gaps) // 2] / 2 if gaps else 0.0
    starts = [beat for beat in beats if start - slack <= beat < end - slack]
    bars = []
    for index, bar_start in enumerate(starts):
        bar_end = starts[index + 1] if index + 1 < len(starts) else end
        first = chord_at(chords, bar_start + 0.05)
        names = [first] if first else []
        late = bar_start + (bar_end - bar_start) / 4
        for chord in chords:
            when = float(chord.get("start", 0))
            name = str(chord.get("name", ""))
            changes = late <= when < bar_end - 0.05
            if changes and name and (not names or names[-1] != name):
                names.append(name)
        bars.append(names[:2] if names else ["N.C."])
    return bars


def chord_grid(bars, per_line=BARS_PER_LINE):
    """Lines like '| D | A | Bm  G | % |'."""
    cells, previous = [], None
    for names in bars:
        cell = "  ".join(names)
        cells.append("%" if cell == previous else cell)
        previous = cell
    width = max((len(cell) for cell in cells), default=1)
    lines = []
    for index in range(0, len(cells), per_line):
        row = cells[index : index + per_line]
        lines.append("| " + " | ".join(cell.ljust(width) for cell in row) + " |")
    return lines


def _clock(seconds):
    seconds = max(0, int(float(seconds or 0)))
    return f"{seconds // 60}:{seconds % 60:02d}"


def sheet_html(title, analysis):
    """The gig sheet as HTML that QTextDocument can lay out on A4."""
    sections = analysis.get("sections", [])
    chords = analysis.get("chords", [])
    downbeats = analysis.get("downbeats", [])
    lyrics = lyrics_per_section(analysis, sections)

    facts = []
    if analysis.get("key"):
        facts.append(escape(str(analysis["key"])))
    if analysis.get("tempo"):
        facts.append(f"{float(analysis['tempo']):.0f} BPM")
    if analysis.get("duration"):
        facts.append(_clock(analysis["duration"]))
    if downbeats:
        facts.append(f"{len(downbeats)} bars")

    html = [
        '<html><body style="color:#000000; background:#FFFFFF;">',
        f'<p style="font-size:18pt; font-weight:700; margin:0;">{escape(title)}</p>',
        f'<p style="font-size:9pt; color:#555555; margin:2px 0 10px 0;">'
        f'{" · ".join(facts)}</p>',
    ]
    for index, section in enumerate(sections):
        start = float(section.get("start", 0))
        end = float(section.get("end", 0))
        name = section_name(sections, index)
        fill = str(section_color(name))  # a hex colour
        ink = text_color_on(fill).name()
        bars = bar_count(downbeats, start, end) if downbeats else 0
        length = f"{_clock(start)}" + (f" · {bars} bars" if bars else "")
        if downbeats:
            grid = chord_grid(bar_chords(chords, downbeats, start, end))
        else:
            grid = ["  ".join(section_chords(chords, start, end))]
        grid_html = "<br>".join(escape(line).replace(" ", "&nbsp;") for line in grid)
        words = (
            escape(lyrics[index]).replace("\n", "<br>") if index < len(lyrics) else ""
        )
        html.append(
            '<table width="100%" cellspacing="0" cellpadding="3"'
            ' style="margin-top:6px; border-collapse:collapse;">'
            f'<tr><td style="background:{fill}; color:{ink};'
            f' font-weight:700; font-size:10pt;">&nbsp;{escape(name)}</td>'
            f'<td align="right" style="background:{fill}; color:{ink};'
            ' font-size:8pt;">'
            f"{length}</td></tr>"
            f'<tr><td colspan="2" style="font-family:Consolas, Menlo, monospace;'
            f' font-size:9.5pt; font-weight:600;">{grid_html}</td></tr>'
            + (
                f'<tr><td colspan="2" style="font-size:9.5pt;">{words}</td></tr>'
                if words
                else ""
            )
            + "</table>"
        )
    html.append("</body></html>")
    return "".join(html)


def a4_layout():
    return QPageLayout(
        QPageSize(QPageSize.PageSizeId.A4),
        QPageLayout.Orientation.Portrait,
        QMarginsF(MARGIN_MM, MARGIN_MM, MARGIN_MM, MARGIN_MM),
        QPageLayout.Unit.Millimeter,
    )


def a4_printer():
    """A printer for the print preview.

    Creating one asks the system for its printers, which can take a long
    time (about 50 seconds over Remote Desktop with redirected printers), so
    PDFs are written with QPdfWriter instead, which never asks.
    """
    from PyQt6.QtPrintSupport import QPrinter

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setPageLayout(a4_layout())
    return printer


def write_pdf(document, path):
    writer = QPdfWriter(str(path))
    writer.setPageLayout(a4_layout())
    writer.setResolution(300)
    writer.setTitle(
        document.metaInformation(QTextDocument.MetaInformation.DocumentTitle)
    )
    document.print(writer)


def sheet_document(title, analysis):
    document = QTextDocument()
    document.setHtml(sheet_html(title, analysis))
    document.setMetaInformation(QTextDocument.MetaInformation.DocumentTitle, title)
    return document


class GigSheet(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        file_menu = window.save_action.associatedObjects()[0]
        self.print_action = QAction("&Print Gig Sheet…", window)
        self.print_action.setShortcut(QKeySequence("Ctrl+P"))
        self.print_action.triggered.connect(self.print_sheet)
        self.pdf_action = QAction("Export Gig Sheet as P&DF…", window)
        self.pdf_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        self.pdf_action.triggered.connect(self.export_pdf)
        for action in (self.print_action, self.pdf_action):
            file_menu.insertAction(window.close_action, action)
        file_menu.insertSeparator(window.close_action)

    def content(self):
        """(title, analysis) for the open song, or None with a message."""
        results = self.window.analysis_results or {}
        analysis = results.get("analysis", {})
        if not self.window.current_file or not analysis.get("sections"):
            QMessageBox.information(
                self.window, "Gig Sheet", "Analyse a song first to make its gig sheet."
            )
            return None
        return Path(self.window.current_file).stem, analysis

    def print_sheet(self):
        from PyQt6.QtPrintSupport import QPrintPreviewDialog

        content = self.content()
        if content is None:
            return
        document = sheet_document(*content)
        self.window.set_status("Contacting printers…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()
        try:
            printer = a4_printer()
        finally:
            QApplication.restoreOverrideCursor()
        self.window.set_status("")
        preview = QPrintPreviewDialog(printer, self.window)
        preview.setWindowTitle(f"Gig sheet: {content[0]}")
        preview.paintRequested.connect(document.print)
        preview.resize(900, 1000)
        preview.exec()

    def export_pdf(self, path=None):
        content = self.content()
        if content is None:
            return None
        if not path:
            suggested = Path(self.window.current_file).with_name(
                f"{content[0]} - gig sheet.pdf"
            )
            path, _ = QFileDialog.getSaveFileName(
                self.window, "Export Gig Sheet", str(suggested), "PDF (*.pdf)"
            )
        if not path:
            return None
        write_pdf(sheet_document(*content), path)
        self.window.set_status(f"Saved gig sheet to {Path(path).name}")
        return path
