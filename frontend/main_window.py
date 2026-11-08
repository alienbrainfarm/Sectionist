#!/usr/bin/env python3
"""
Main Window Module for Sectionist GUI

This module contains the SectionistMainWindow class that provides
the main application window and user interface logic.
"""

import json
import shutil
from pathlib import Path
from typing import Dict

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLabel,
    QFileDialog,
    QProgressBar,
    QTextEdit,
    QSplitter,
    QStackedWidget,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QAction, QKeySequence

try:
    # Try relative imports first (when run as module)
    from .analysis_worker import AnalysisWorker
    from .audio_player import AudioPlayer
    from .timeline_widget import TimelineWidget
    from .lyrics_view import create_lyrics_dock, show_lyrics
    from .results_text import format_details
    from .stem_lanes import StemLanes, TimelineGutter
    from .controllers import Addons
    from .panels import (
        EmptyState,
        HeaderBar,
        SectionsTable,
        TransportBar,
        format_clock,
        make_card,
        song_meta,
    )
except ImportError:
    # Fall back to absolute imports (when run directly)
    from analysis_worker import AnalysisWorker
    from audio_player import AudioPlayer
    from timeline_widget import TimelineWidget
    from lyrics_view import create_lyrics_dock, show_lyrics
    from results_text import format_details
    from stem_lanes import StemLanes, TimelineGutter
    from controllers import Addons
    from panels import (
        EmptyState,
        HeaderBar,
        SectionsTable,
        TransportBar,
        format_clock,
        make_card,
        song_meta,
    )

AUDIO_EXTENSIONS = {".mp3", ".wav", ".aiff", ".aif", ".m4a", ".flac", ".ogg", ".aac"}
ANALYZING_HINT = "Finding sections, chords and lyrics…"


class SectionistMainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.current_file = None
        self.analysis_results = None
        self.audio_player = AudioPlayer()
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback_position)
        self.recent_files = []  # Store recent files

        self.init_ui()
        self.setAcceptDrops(True)  # Enable drag & drop

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Sectionist")
        self.resize(1280, 820)
        self.setMinimumSize(820, 560)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setCentralWidget(central)

        self.header = HeaderBar()
        self.header.open_button.clicked.connect(self.browse_file)
        self.header.analyze_button.clicked.connect(self.analyze_audio)
        root.addWidget(self.header)

        # Two pages: a drop target before a song is open, the workspace after.
        self.pages = QStackedWidget()
        root.addWidget(self.pages, 1)

        self.empty_state = EmptyState()
        self.empty_state.open_requested.connect(self.browse_file)
        self.empty_state.load_requested.connect(self.load_song)
        self.empty_state.recent_requested.connect(self.load_file)
        self.pages.addWidget(self.empty_state)

        self.workspace = self.build_workspace()
        self.pages.addWidget(self.workspace)

        self.build_status_bar()
        self.create_menu_bar()

        # Lyrics live in a dock so they can be hidden or floated without
        # disturbing the section and chord layout.
        self.lyrics_dock, self.lyrics_text = create_lyrics_dock(self)
        self.lyrics_dock.visibilityChanged.connect(self.toggle_lyrics_action.setChecked)
        self.addons = Addons(self)  # stems, cycle, locks, export, gig sheet

    def build_workspace(self):
        """Timeline card on top, sections and details side by side below."""
        workspace = QWidget()
        workspace.setObjectName("Workspace")
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(18, 8, 18, 14)

        # Timeline with the transport underneath
        timeline_card, timeline_layout = make_card()
        self.timeline = TimelineWidget()
        self.timeline.section_clicked.connect(self.seek_to_position)
        self.timeline.section_renamed.connect(self.rename_section)
        self.timeline.section_resized.connect(self.resize_section)
        self.timeline.section_separator_moved.connect(self.move_section_separator)
        self.timeline.section_joined.connect(self.join_section_with_next)
        self.timeline.section_split.connect(self.split_section)
        self.timeline.chord_renamed.connect(self.rename_chord)
        self.timeline.chord_boundary_moved.connect(self.move_chord_boundary)
        # While stems are shown, the timeline gets a gutter matching the
        # stem lanes' controls so every lane shares one time axis.
        timeline_row = QHBoxLayout()
        timeline_row.setSpacing(0)  # the stem rows have none either
        self.timeline_gutter = TimelineGutter(self.timeline)
        timeline_row.addWidget(self.timeline_gutter)
        timeline_row.addWidget(self.timeline, 1)
        timeline_layout.addLayout(timeline_row, 1)
        self.stem_lanes = StemLanes()
        timeline_layout.addWidget(self.stem_lanes)

        self.transport = TransportBar()
        self.play_button = self.transport.play_button
        self.stop_button = self.transport.stop_button
        self.position_slider = self.transport.position_slider
        self.time_label = self.transport.time_label
        self.play_button.clicked.connect(self.toggle_playback)
        self.stop_button.clicked.connect(self.stop_playback)
        self.position_slider.sliderPressed.connect(self.slider_pressed)
        self.position_slider.sliderReleased.connect(self.slider_released)
        self.position_slider.valueChanged.connect(self.slider_value_changed)
        self.slider_is_pressed = False
        timeline_layout.addWidget(self.transport)

        # Results area
        self.results_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.results_splitter.setHandleWidth(12)

        self.sections_group, sections_layout = make_card("Sections")
        self.sections_table = SectionsTable()
        self.sections_table.section_activated.connect(self.seek_to_section)
        self.sections_table.rename_requested.connect(self.timeline.start_rename_section)
        sections_layout.addWidget(self.sections_table)

        self.details_group, details_layout = make_card("Analysis")
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setFrameShape(QTextEdit.Shape.NoFrame)
        details_layout.addWidget(self.details_text)

        self.results_splitter.addWidget(self.sections_group)
        self.results_splitter.addWidget(self.details_group)
        self.results_splitter.setStretchFactor(0, 3)
        self.results_splitter.setStretchFactor(1, 2)
        self.results_splitter.setSizes([700, 420])

        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.setHandleWidth(12)
        vertical.setChildrenCollapsible(False)
        vertical.addWidget(timeline_card)
        vertical.addWidget(self.results_splitter)
        vertical.setStretchFactor(0, 1)
        vertical.setStretchFactor(1, 1)
        vertical.setSizes([330, 320])
        layout.addWidget(vertical, 1)
        return workspace

    def build_status_bar(self):
        """Progress and messages live in the status bar, out of the way."""
        self.status_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(160)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.addWidget(self.status_label, 1)
        status.addPermanentWidget(self.progress_bar)

    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        def action(menu, text, slot, shortcut=None, enabled=True):
            item = QAction(text, self)
            if shortcut:
                item.setShortcut(QKeySequence(shortcut))
            item.triggered.connect(slot)
            item.setEnabled(enabled)
            menu.addAction(item)
            return item

        file_menu = menubar.addMenu("&File")
        action(file_menu, "&Open Audio File…", self.browse_file, "Ctrl+O")
        action(file_menu, "&Load Song…", self.load_song, "Ctrl+L")
        self.recent_menu = file_menu.addMenu("Load &Recent")
        self.update_recent_menu()
        file_menu.addSeparator()
        self.save_action = action(
            file_menu, "&Save Song…", self.save_song, "Ctrl+S", enabled=False
        )
        self.close_action = action(
            file_menu, "&Close Song", self.clear_file, "Ctrl+W", enabled=False
        )
        file_menu.addSeparator()
        action(file_menu, "&Quit", self.close, "Ctrl+Q")

        self.playback_menu = playback_menu = menubar.addMenu("&Playback")
        self.play_action = action(
            playback_menu, "Play / Pause", self.toggle_playback, "Space", False
        )
        self.stop_action = action(
            playback_menu, "Stop", self.stop_playback, "Ctrl+.", False
        )

        self.analysis_menu = analysis_menu = menubar.addMenu("&Analysis")
        self.analyze_action = action(
            analysis_menu, "&Analyze Audio", self.analyze_audio, "Ctrl+R", False
        )

        view_menu = menubar.addMenu("&View")
        self.toggle_sections_action = action(
            view_menu, "Sections Panel", self.toggle_sections_panel
        )
        self.toggle_details_action = action(
            view_menu, "Analysis Panel", self.toggle_details_panel
        )
        self.toggle_lyrics_action = action(
            view_menu, "Lyrics Panel", self.toggle_lyrics_panel
        )
        for item in (
            self.toggle_sections_action,
            self.toggle_details_action,
            self.toggle_lyrics_action,
        ):
            item.setCheckable(True)
            item.setChecked(True)
        self.toggle_lyrics_action.setChecked(False)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and self.is_audio_file(urls[0].toLocalFile()):
                event.accept()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        urls = event.mimeData().urls()
        if len(urls) == 1:
            file_path = urls[0].toLocalFile()
            if self.is_audio_file(file_path):
                self.load_file(file_path)
                event.accept()
            else:
                event.ignore()

    def is_audio_file(self, file_path: str) -> bool:
        """Check if the file is a supported audio format."""
        return Path(file_path).suffix.lower() in AUDIO_EXTENSIONS

    def browse_file(self):
        """Open file browser to select an audio file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            "",
            "Audio Files (*.mp3 *.wav *.aiff *.aif *.m4a *.flac *.ogg "
            "*.aac);;All Files (*)",
        )

        if file_path:
            self.load_file(file_path)

    def set_status(self, message: str):
        self.status_label.setText(message)

    def set_playback_enabled(self, enabled: bool):
        for widget in (
            self.play_button,
            self.stop_button,
            self.position_slider,
            self.play_action,
            self.stop_action,
        ):
            widget.setEnabled(enabled)

    def load_file(self, file_path: str, auto_analyze: bool = True):
        """Load an audio file."""
        self.current_file = file_path
        title = Path(file_path).stem
        self.setWindowTitle(f"{title} — Sectionist")

        # Update UI
        self.analyze_action.setEnabled(True)
        self.header.analyze_button.setEnabled(True)
        self.save_action.setEnabled(False)  # Enable after analysis
        self.close_action.setEnabled(True)
        self.pages.setCurrentWidget(self.workspace)

        # A new file must not show the previous song's analysis.
        self.analysis_results = None
        self.display_results({"success": True, "analysis": {}})
        self.addons.song_changed(file_path)

        # Load into audio player
        if self.audio_player.load_file(file_path):
            self.set_playback_enabled(True)
            self.position_slider.setMaximum(int(self.audio_player.duration))
            self.timeline.set_duration(self.audio_player.duration)
            self.update_time_label()
        self.header.set_song(title, song_meta(None, self.audio_player.duration))

        # Auto-analyze audio when file is first opened (unless loading saved data)
        if auto_analyze:
            self.analyze_audio()

    def clear_file(self):
        """Close the current song and return to the start page."""
        self.current_file = None
        self.analysis_results = None

        # Stop playback
        self.stop_playback()
        self.addons.song_changed(None)

        # Reset UI
        self.setWindowTitle("Sectionist")
        self.header.set_song(
            "Sectionist", "Open a song to find its sections, key and chords"
        )
        self.header.analyze_button.setEnabled(False)
        self.analyze_action.setEnabled(False)
        self.save_action.setEnabled(False)
        self.close_action.setEnabled(False)
        self.set_playback_enabled(False)
        self.transport.set_section("")

        # Clear results
        self.display_results({"success": True, "analysis": {}})
        self.timeline.set_duration(0)
        self.lyrics_dock.hide()

        self.pages.setCurrentWidget(self.empty_state)
        self.set_status("Ready")

    def analyze_audio(self):
        """Start audio analysis."""
        if not self.current_file:
            return

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.analyze_action.setEnabled(False)
        self.header.analyze_button.setEnabled(False)
        self.header.analyze_button.setText("Analyzing…")
        self.timeline.placeholder_text = ANALYZING_HINT
        self.timeline.update()
        self.set_status("Starting analysis…")

        # Start analysis worker
        self.analysis_worker = AnalysisWorker(self.current_file)
        self.analysis_worker.finished.connect(self.analysis_finished)
        self.analysis_worker.error.connect(self.analysis_error)
        self.analysis_worker.progress.connect(self.analysis_progress)
        self.analysis_worker.start()

    def end_analysis(self, placeholder: str = ""):
        """Put the analysis controls back after success or failure."""
        self.progress_bar.setVisible(False)
        self.analyze_action.setEnabled(True)
        self.header.analyze_button.setEnabled(True)
        self.header.analyze_button.setText("Analyze")
        self.timeline.placeholder_text = placeholder
        self.timeline.update()

    def analysis_progress(self, message: str):
        """Update analysis progress."""
        self.set_status(message)

    def analysis_finished(self, results: Dict):
        """Handle completed analysis."""
        self.analysis_results = results = self.addons.keep_locked(results)
        self.end_analysis()
        self.save_action.setEnabled(True)  # Enable save after analysis
        self.set_status("Analysis complete")

        # Show results
        self.display_results(results)
        self.addons.analysis_finished(results)

        # Add to recent files
        if self.current_file:
            self.add_to_recent_files(self.current_file)

    def analysis_error(self, error_message: str):
        """Handle analysis error."""
        self.end_analysis("Analysis failed. Press Analyze to try again.")
        self.set_status(f"Error: {error_message}")

        # Show error dialog
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Analysis Error")
        msg.setText("Audio analysis failed")
        msg.setInformativeText(error_message)
        msg.exec()

    def display_results(self, results: Dict):
        """Display analysis results in the UI."""
        if not results.get("success"):
            return

        analysis = results.get("analysis", {})

        sections = analysis.get("sections", [])
        chords = analysis.get("chords", [])
        downbeats = analysis.get("downbeats", [])
        self.sections_table.populate(sections, chords, downbeats)
        self.details_text.setHtml(format_details(analysis) if analysis else "")

        # Update timeline
        self.timeline.set_sections(sections)
        self.timeline.set_chords(chords)
        self.timeline.set_downbeats(downbeats)
        self.stem_lanes.set_sections(sections)

        if self.current_file and analysis:
            self.header.set_song(
                Path(self.current_file).stem,
                song_meta(analysis, self.audio_player.duration),
            )
        self.update_current_section()

        show_lyrics(
            self.lyrics_dock,
            self.lyrics_text,
            self.toggle_lyrics_action,
            analysis,
            sections,
        )

    def format_time(self, seconds: float) -> str:
        """Format time in M:SS format."""
        return format_clock(seconds)

    def toggle_playback(self):
        """Toggle play/pause."""
        if not self.current_file:
            return
        if self.audio_player.is_playing:
            self.audio_player.pause()
            self.playback_timer.stop()
        else:
            self.audio_player.play()
            self.playback_timer.start(50)
        self.transport.set_playing(self.audio_player.is_playing)

    def stop_playback(self):
        """Stop playback."""
        self.audio_player.stop()
        self.transport.set_playing(False)
        self.playback_timer.stop()
        self.position_slider.setValue(0)
        self.timeline.set_position(0)
        self.update_time_label()
        self.update_current_section()

    def seek_to_position(self, timestamp: float):
        """Seek to a specific position."""
        self.audio_player.set_position(timestamp)
        # VLC reports the new position asynchronously, so move the playhead
        # straight away rather than waiting for the next poll.
        self.timeline.set_position(timestamp)
        self.position_slider.setValue(int(timestamp))
        self.update_time_label(timestamp)
        self.update_current_section()

    def seek_to_section(self, section_idx: int):
        """Jump to the start of a section (from the sections table)."""
        sections = self.timeline.sections
        if 0 <= section_idx < len(sections):
            self.seek_to_position(float(sections[section_idx].get("start", 0)))

    def slider_pressed(self):
        """Handle slider press (pause updates)."""
        self.slider_is_pressed = True
        self.playback_timer.stop()

    def slider_released(self):
        """Handle slider release (resume updates)."""
        self.slider_is_pressed = False
        if self.audio_player.is_playing:
            self.playback_timer.start(50)

    def slider_value_changed(self, value):
        """Handle slider value change (seeking)."""
        if self.slider_is_pressed:  # Only seek when user is dragging
            timestamp = float(value)
            self.audio_player.set_position(timestamp)
            self.timeline.set_position(timestamp)
            self.update_time_label(timestamp)
            self.update_current_section()

    def update_playback_position(self):
        """Update playback position indicators."""
        self.audio_player.apply_pending_seek()
        if not self.slider_is_pressed:  # Only update if user is not dragging slider
            position = self.audio_player.get_position()
            self.position_slider.setValue(int(position))
            self.timeline.set_position(position)
        self.update_time_label()
        self.update_current_section()

    def update_current_section(self):
        """Show the section under the playhead next to the clock."""
        index = self.timeline.current_section()
        name = self.timeline.sections[index].get("name", "") if index >= 0 else ""
        self.transport.set_section(name)

    def update_time_label(self, current: float = None):
        """Update the time display label."""
        if current is None:
            current = self.audio_player.get_position()
        total = self.audio_player.get_duration()
        self.time_label.setText(
            f"{self.format_time(current)} / {self.format_time(total)}"
        )

    def save_song(self):
        """Save the current song and analysis data."""
        if not self.current_file or not self.analysis_results:
            QMessageBox.warning(
                self,
                "Save Song",
                "No analysis data to save. Please analyze an audio file first.",
            )
            return

        folder = QFileDialog.getExistingDirectory(
            self, "Save Song", "", QFileDialog.Option.ShowDirsOnly
        )

        if folder:
            try:
                # Create song folder structure
                song_name = Path(self.current_file).stem
                song_folder = Path(folder) / song_name
                song_folder.mkdir(exist_ok=True)

                # Copy audio file
                audio_dest = song_folder / Path(self.current_file).name
                shutil.copy2(self.current_file, audio_dest)

                # Save analysis data
                analysis_file = song_folder / "analysis.json"
                with open(analysis_file, "w") as f:
                    saved = dict(self.analysis_results, **self.addons.saved())
                    json.dump(saved, f, indent=2)

                self.set_status(f"Saved to {song_folder}")

            except Exception as e:
                QMessageBox.critical(
                    self, "Save Song", f"Failed to save song:\n{str(e)}"
                )

    def load_song(self):
        """Load a previously saved song."""
        folder = QFileDialog.getExistingDirectory(
            self, "Load Song", "", QFileDialog.Option.ShowDirsOnly
        )

        if folder:
            self.load_song_from_folder(folder)

    def load_song_from_folder(self, folder):
        """Load song from a specific folder."""
        try:
            folder_path = Path(folder)
            analysis_file = folder_path / "analysis.json"

            if not analysis_file.exists():
                QMessageBox.warning(
                    self, "Load Song", "No analysis data found in selected folder."
                )
                return

            # Find audio file
            audio_files = [
                f for f in folder_path.iterdir() if f.suffix.lower() in AUDIO_EXTENSIONS
            ]

            if not audio_files:
                QMessageBox.warning(
                    self, "Load Song", "No audio file found in selected folder."
                )
                return

            # Load analysis data
            with open(analysis_file, "r") as f:
                results = json.load(f)

            # Load audio file without auto-analyzing (this resets the panels)
            self.load_file(str(audio_files[0]), auto_analyze=False)

            # Display results without re-analyzing
            self.analysis_results = results
            self.display_results(self.analysis_results)
            self.addons.song_loaded(results)
            self.save_action.setEnabled(True)
            self.set_status(f"Loaded {folder_path.name}")

        except Exception as e:
            QMessageBox.critical(self, "Load Song", f"Failed to load song:\n{str(e)}")

    def add_to_recent_files(self, file_path):
        """Add file to recent files list."""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)

        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:10]  # Keep only 10 recent files
        self.update_recent_menu()
        self.save_recent_files()

    def update_recent_menu(self):
        """Update the recent files menu."""
        self.recent_menu.clear()
        if hasattr(self, "empty_state"):
            self.empty_state.set_recent(self.recent_files)

        if not self.recent_files:
            action = QAction("No recent files", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
            return

        for file_path in self.recent_files:
            if Path(file_path).exists():
                filename = Path(file_path).name
                action = QAction(filename, self)
                action.triggered.connect(
                    lambda checked, fp=file_path: self.load_file(fp)
                )
                self.recent_menu.addAction(action)

    def save_recent_files(self):
        """Save recent files list to disk."""
        try:
            recent_file = Path.home() / ".sectionist_recent.json"
            with open(recent_file, "w") as f:
                json.dump(self.recent_files, f)
        except Exception:
            pass  # Silently fail if can't save recent files

    def load_recent_files(self):
        """Load recent files list from disk."""
        try:
            recent_file = Path.home() / ".sectionist_recent.json"
            if recent_file.exists():
                with open(recent_file, "r") as f:
                    self.recent_files = json.load(f)
                self.update_recent_menu()
        except Exception:
            pass  # Silently fail if can't load recent files

    def shutdown(self):
        """Release playback and background work so the process can exit."""
        try:
            self.playback_timer.stop()
        except Exception:
            pass

        for step in (self.audio_player.stop, self.addons.shutdown):
            try:
                step()
            except Exception:
                pass

        worker = getattr(self, "analysis_worker", None)
        if worker is not None and worker.isRunning():
            worker.requestInterruption()
            worker.quit()
            if not worker.wait(2000):
                worker.terminate()
                worker.wait(500)

    def toggle_lyrics_panel(self):
        """Show or hide the lyrics dock."""
        self.lyrics_dock.setVisible(self.toggle_lyrics_action.isChecked())

    def toggle_sections_panel(self):
        """Show or hide the sections table."""
        self.sections_group.setVisible(self.toggle_sections_action.isChecked())

    def toggle_details_panel(self):
        """Show or hide the analysis details."""
        self.details_group.setVisible(self.toggle_details_action.isChecked())

    def chord_list(self):
        """The live chord list inside the current analysis results."""
        return (self.analysis_results or {}).get("analysis", {}).get("chords", [])

    def rename_chord(self, chord_idx, new_name):
        """Rename a chord and refresh the panel."""
        chords = self.chord_list()
        if 0 <= chord_idx < len(chords):
            chords[chord_idx]["name"] = new_name
            self.display_results(self.analysis_results)
            self.status_label.setText(f"Chord {chord_idx + 1} renamed to '{new_name}'")

    def move_chord_boundary(self, boundary_idx, new_time):
        """Move the boundary between two chords, keeping them contiguous."""
        chords = self.chord_list()
        if not 0 <= boundary_idx < len(chords) - 1:
            return

        left = chords[boundary_idx]
        right = chords[boundary_idx + 1]
        lower = float(left.get("start", 0)) + 0.05
        upper = float(right.get("end", 0)) - 0.05
        if upper <= lower:
            return

        boundary = round(max(lower, min(float(new_time), upper)), 2)
        left["end"] = boundary
        right["start"] = boundary
        # The timeline holds the same list objects, so a repaint is enough
        # during a drag; the panel catches up on rename/analysis.
        self.timeline.update()

    def rename_section(self, section_idx, new_name):
        """Rename a section."""
        if not self.analysis_results or section_idx < 0:
            return

        sections = self.analysis_results.get("analysis", {}).get("sections", [])
        if section_idx < len(sections):
            sections[section_idx]["name"] = new_name

            # Update displays
            self.display_results(self.analysis_results)
            self.timeline.set_sections(sections)

            # Mark as modified (could save automatically or flag for save)
            self.status_label.setText(
                f"Section {section_idx + 1} renamed to '{new_name}'"
            )

    def resize_section(self, section_idx, new_start, new_end):
        """Resize a section."""
        if not self.analysis_results or section_idx < 0:
            return

        sections = self.analysis_results.get("analysis", {}).get("sections", [])
        if section_idx < len(sections):
            sections[section_idx]["start"] = new_start
            sections[section_idx]["end"] = new_end

            # Update displays
            self.display_results(self.analysis_results)
            self.timeline.set_sections(sections)

            # Mark as modified
            self.status_label.setText(f"Section {section_idx + 1} resized")

    def move_section_separator(self, separator_idx, new_time):
        """Move a section separator, affecting both adjacent sections."""
        if not self.analysis_results or separator_idx < 0:
            return

        sections = self.analysis_results.get("analysis", {}).get("sections", [])
        if separator_idx < len(sections) - 1:  # Ensure there's a next section
            # Update the end of the current section and start of the next section
            sections[separator_idx]["end"] = new_time
            sections[separator_idx + 1]["start"] = new_time

            # Update displays
            self.display_results(self.analysis_results)
            self.timeline.set_sections(sections)

            # Mark as modified
            self.status_label.setText(
                f"Separator between sections {separator_idx + 1} and "
                f"{separator_idx + 2} moved"
            )

    def join_section_with_next(self, section_idx):
        """Join a section with the next section."""
        if not self.analysis_results or section_idx < 0:
            return

        sections = self.analysis_results.get("analysis", {}).get("sections", [])
        if (
            section_idx < len(sections) - 1
        ):  # Ensure there's a next section to join with
            current_section = sections[section_idx]
            next_section = sections[section_idx + 1]

            # Extend current section to include the next section's end time
            current_section["end"] = next_section["end"]

            # Remove the next section
            sections.pop(section_idx + 1)

            # Update displays
            self.display_results(self.analysis_results)
            self.timeline.set_sections(sections)

            # Mark as modified
            self.status_label.setText(
                f"Section {section_idx + 1} joined with next section"
            )

    def split_section(self, section_idx, split_time):
        """Split a section into two sections at the specified time."""
        if not self.analysis_results or section_idx < 0:
            return

        sections = self.analysis_results.get("analysis", {}).get("sections", [])
        if section_idx < len(sections):
            current_section = sections[section_idx]

            # Create new section for the second half
            new_section = {
                "start": split_time,
                "end": current_section["end"],
                "name": current_section["name"] + " (2)",  # Add suffix to distinguish
            }

            # Update current section to end at split time
            current_section["end"] = split_time

            # Insert the new section after the current one
            sections.insert(section_idx + 1, new_section)

            # Update displays
            self.display_results(self.analysis_results)
            self.timeline.set_sections(sections)

            # Mark as modified
            self.status_label.setText(
                f"Section {section_idx + 1} split into two sections"
            )
