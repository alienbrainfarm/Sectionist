#!/usr/bin/env python3
"""
Sectionist - Python Frontend Prototype

A cross-platform audio analysis frontend built with PyQt6 to replace the Swift frontend.
This provides the same functionality as the Swift version but works on Windows, macOS, and Linux.

Features:
- Drag & drop audio file support
- Communication with existing Python backend
- Audio playback controls
- Timeline visualization
- Analysis results display
- Cross-platform compatibility
"""

import sys
import os
import json
import requests
import threading
import time
from pathlib import Path
from typing import Optional, Dict, List

# Audio and GUI libraries
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
        QPushButton, QLabel, QFileDialog, QProgressBar, QTextEdit,
        QSlider, QComboBox, QSplitter, QFrame, QGroupBox, QMessageBox,
        QGridLayout, QSpacerItem, QSizePolicy
    )
    from PyQt6.QtCore import (
        Qt, QThread, pyqtSignal, QTimer, QMimeData, QUrl
    )
    from PyQt6.QtGui import (
        QFont, QPixmap, QIcon, QDragEnterEvent, QDropEvent, QPalette
    )
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PyQt6.QtMultimediaWidgets import QVideoWidget
except ImportError:
    print("PyQt6 not found. Install with: pip install PyQt6")
    sys.exit(1)

try:
    import pygame
except ImportError:
    print("pygame not found. Install with: pip install pygame")
    sys.exit(1)

try:
    from mutagen import File as MutagenFile
except ImportError:
    print("mutagen not found. Install with: pip install mutagen")
    sys.exit(1)


class AnalysisWorker(QThread):
    """Worker thread for analyzing audio files with the backend."""
    
    finished = pyqtSignal(dict)  # Analysis results
    error = pyqtSignal(str)      # Error message
    progress = pyqtSignal(str)   # Progress updates
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.backend_url = "http://127.0.0.1:5000"
    
    def run(self):
        """Run the analysis in a background thread."""
        try:
            self.progress.emit("Checking backend connection...")
            
            # Check if backend is running
            health_response = requests.get(f"{self.backend_url}/health", timeout=5)
            if health_response.status_code != 200:
                self.error.emit("Backend server is not responding")
                return
            
            self.progress.emit("Uploading file for analysis...")
            
            # Analyze the audio file
            with open(self.file_path, 'rb') as f:
                files = {'audio': f}
                response = requests.post(
                    f"{self.backend_url}/analyze", 
                    files=files, 
                    timeout=60
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.progress.emit("Analysis completed successfully!")
                    self.finished.emit(result)
                else:
                    self.error.emit(f"Analysis failed: {result.get('error', 'Unknown error')}")
            else:
                self.error.emit(f"Server error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.error.emit("Analysis request timed out")
        except requests.exceptions.ConnectionError:
            self.error.emit("Cannot connect to backend server. Make sure it's running on port 5000.")
        except Exception as e:
            self.error.emit(f"Analysis error: {str(e)}")


class AudioPlayer:
    """Simple audio player using pygame."""
    
    def __init__(self):
        pygame.mixer.init()
        self.is_playing = False
        self.is_paused = False
        self.current_file = None
        self.duration = 0
        self.position = 0
        
    def load_file(self, file_path: str) -> bool:
        """Load an audio file."""
        try:
            # Get file duration using mutagen
            audio_file = MutagenFile(file_path)
            if audio_file is not None:
                self.duration = audio_file.info.length
            else:
                self.duration = 0
            
            pygame.mixer.music.load(file_path)
            self.current_file = file_path
            self.position = 0
            return True
        except Exception as e:
            print(f"Error loading audio file: {e}")
            return False
    
    def play(self):
        """Start or resume playback."""
        if self.current_file:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
            else:
                pygame.mixer.music.play()
            self.is_playing = True
    
    def pause(self):
        """Pause playback."""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False
    
    def stop(self):
        """Stop playback."""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.position = 0
    
    def set_position(self, position: float):
        """Set playback position (limited functionality with pygame)."""
        # pygame doesn't support seeking, this is a limitation
        # In a production version, we'd use a different audio library
        pass
    
    def get_position(self) -> float:
        """Get current playback position."""
        # This is a simplified implementation
        return self.position
    
    def get_duration(self) -> float:
        """Get total duration."""
        return self.duration


class TimelineWidget(QWidget):
    """Timeline visualization widget."""
    
    section_clicked = pyqtSignal(float)  # Emit timestamp when section is clicked
    
    def __init__(self):
        super().__init__()
        self.sections = []
        self.duration = 0
        self.current_position = 0
        self.setMinimumHeight(100)
        self.setStyleSheet("""
            TimelineWidget {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
    
    def set_sections(self, sections: List[Dict]):
        """Set the song sections to display."""
        self.sections = sections
        self.update()
    
    def set_duration(self, duration: float):
        """Set the total duration."""
        self.duration = duration
        self.update()
    
    def set_position(self, position: float):
        """Set the current playback position."""
        self.current_position = position
        self.update()
    
    def paintEvent(self, event):
        """Paint the timeline."""
        from PyQt6.QtGui import QPainter, QColor, QPen
        
        painter = QPainter(self)
        rect = self.rect()
        
        # Background
        painter.fillRect(rect, QColor(240, 240, 240))
        
        if self.duration > 0 and self.sections:
            # Draw sections
            colors = [
                QColor(100, 150, 255),  # Blue for intro
                QColor(100, 255, 150),  # Green for verse
                QColor(255, 150, 100),  # Orange for chorus
                QColor(200, 100, 255),  # Purple for bridge
                QColor(255, 100, 100),  # Red for outro
            ]
            
            for i, section in enumerate(self.sections):
                start_time = section.get('start', 0)
                end_time = section.get('end', 0)
                name = section.get('name', 'Section')
                
                # Calculate position and width
                x = int((start_time / self.duration) * rect.width())
                width = int(((end_time - start_time) / self.duration) * rect.width())
                
                # Choose color
                color = colors[i % len(colors)]
                painter.fillRect(x, 0, width, rect.height(), color)
                
                # Draw section label
                painter.setPen(QPen(QColor(0, 0, 0)))
                if width > 50:  # Only draw text if there's enough space
                    painter.drawText(x + 5, 20, name)
        
        # Draw current position indicator
        if self.duration > 0:
            pos_x = int((self.current_position / self.duration) * rect.width())
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.drawLine(pos_x, 0, pos_x, rect.height())
    
    def mousePressEvent(self, event):
        """Handle mouse clicks on the timeline."""
        if self.duration > 0:
            click_x = event.position().x()
            timestamp = (click_x / self.width()) * self.duration
            self.section_clicked.emit(timestamp)


class SectionistMainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.analysis_results = None
        self.audio_player = AudioPlayer()
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback_position)
        
        self.init_ui()
        self.setAcceptDrops(True)  # Enable drag & drop
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Sectionist - Audio Analysis Tool")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Header
        header_layout = QVBoxLayout()
        title_label = QLabel("Sectionist")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_label = QLabel("Analyze your songs • Visualize structure • Understand harmony")
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addLayout(header_layout)
        
        # File selection area
        self.file_group = QGroupBox("Audio File")
        file_layout = QHBoxLayout(self.file_group)
        
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_file)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_file)
        self.clear_button.setEnabled(False)
        
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(self.browse_button)
        file_layout.addWidget(self.clear_button)
        
        layout.addWidget(self.file_group)
        
        # Analysis controls
        analysis_layout = QHBoxLayout()
        
        self.analyze_button = QPushButton("Analyze Audio")
        self.analyze_button.clicked.connect(self.analyze_audio)
        self.analyze_button.setEnabled(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666;")
        
        analysis_layout.addWidget(self.analyze_button)
        analysis_layout.addWidget(self.progress_bar)
        analysis_layout.addWidget(self.status_label, 1)
        
        layout.addLayout(analysis_layout)
        
        # Timeline and playback controls
        self.timeline_group = QGroupBox("Timeline & Playback")
        timeline_layout = QVBoxLayout(self.timeline_group)
        
        # Timeline widget
        self.timeline = TimelineWidget()
        self.timeline.section_clicked.connect(self.seek_to_position)
        timeline_layout.addWidget(self.timeline)
        
        # Playback controls
        playback_layout = QHBoxLayout()
        
        self.play_button = QPushButton("▶ Play")
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setEnabled(False)
        
        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.clicked.connect(self.stop_playback)
        self.stop_button.setEnabled(False)
        
        # Position slider
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.sliderPressed.connect(self.slider_pressed)
        self.position_slider.sliderReleased.connect(self.slider_released)
        self.position_slider.setEnabled(False)
        
        self.time_label = QLabel("00:00 / 00:00")
        
        playback_layout.addWidget(self.play_button)
        playback_layout.addWidget(self.stop_button)
        playback_layout.addWidget(self.position_slider, 1)
        playback_layout.addWidget(self.time_label)
        
        timeline_layout.addLayout(playback_layout)
        layout.addWidget(self.timeline_group)
        
        # Results area
        self.results_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sections list
        self.sections_group = QGroupBox("Song Sections")
        sections_layout = QVBoxLayout(self.sections_group)
        self.sections_text = QTextEdit()
        self.sections_text.setReadOnly(True)
        sections_layout.addWidget(self.sections_text)
        
        # Analysis details
        self.details_group = QGroupBox("Analysis Details")
        details_layout = QVBoxLayout(self.details_group)
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        
        self.results_splitter.addWidget(self.sections_group)
        self.results_splitter.addWidget(self.details_group)
        self.results_splitter.setSizes([400, 400])
        
        layout.addWidget(self.results_splitter)
        
        # Drop area label (shown when no file)
        self.drop_label = QLabel("Drop an audio file here or click Browse")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 10px;
                padding: 40px;
                font-size: 16px;
                color: #666;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(self.drop_label)
        
        # Hide results initially
        self.timeline_group.setVisible(False)
        self.results_splitter.setVisible(False)
    
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
        audio_extensions = {'.mp3', '.wav', '.aiff', '.aif', '.m4a', '.flac', '.ogg', '.aac'}
        return Path(file_path).suffix.lower() in audio_extensions
    
    def browse_file(self):
        """Open file browser to select an audio file."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Select Audio File",
            "",
            "Audio Files (*.mp3 *.wav *.aiff *.aif *.m4a *.flac *.ogg *.aac);;All Files (*)"
        )
        
        if file_path:
            self.load_file(file_path)
    
    def load_file(self, file_path: str):
        """Load an audio file."""
        self.current_file = file_path
        filename = Path(file_path).name
        
        # Update UI
        self.file_label.setText(filename)
        self.file_label.setStyleSheet("QLabel { color: black; font-weight: bold; }")
        self.analyze_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.drop_label.setVisible(False)
        
        # Load into audio player
        if self.audio_player.load_file(file_path):
            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.position_slider.setEnabled(True)
            self.position_slider.setMaximum(int(self.audio_player.duration))
            self.timeline.set_duration(self.audio_player.duration)
            self.update_time_label()
        
        # Show timeline group
        self.timeline_group.setVisible(True)
    
    def clear_file(self):
        """Clear the current file."""
        self.current_file = None
        self.analysis_results = None
        
        # Stop playback
        self.stop_playback()
        
        # Reset UI
        self.file_label.setText("No file selected")
        self.file_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        self.analyze_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.position_slider.setEnabled(False)
        
        # Clear results
        self.sections_text.clear()
        self.details_text.clear()
        
        # Hide groups and show drop area
        self.timeline_group.setVisible(False)
        self.results_splitter.setVisible(False)
        self.drop_label.setVisible(True)
    
    def analyze_audio(self):
        """Start audio analysis."""
        if not self.current_file:
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.analyze_button.setEnabled(False)
        self.status_label.setText("Starting analysis...")
        
        # Start analysis worker
        self.analysis_worker = AnalysisWorker(self.current_file)
        self.analysis_worker.finished.connect(self.analysis_finished)
        self.analysis_worker.error.connect(self.analysis_error)
        self.analysis_worker.progress.connect(self.analysis_progress)
        self.analysis_worker.start()
    
    def analysis_progress(self, message: str):
        """Update analysis progress."""
        self.status_label.setText(message)
    
    def analysis_finished(self, results: Dict):
        """Handle completed analysis."""
        self.analysis_results = results
        
        # Hide progress
        self.progress_bar.setVisible(False)
        self.analyze_button.setEnabled(True)
        self.status_label.setText("Analysis completed!")
        
        # Show results
        self.display_results(results)
        self.results_splitter.setVisible(True)
    
    def analysis_error(self, error_message: str):
        """Handle analysis error."""
        # Hide progress
        self.progress_bar.setVisible(False)
        self.analyze_button.setEnabled(True)
        self.status_label.setText(f"Error: {error_message}")
        
        # Show error dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Analysis Error")
        msg.setText("Audio analysis failed")
        msg.setDetailedText(error_message)
        msg.exec()
    
    def display_results(self, results: Dict):
        """Display analysis results in the UI."""
        if not results.get('success'):
            return
        
        analysis = results.get('analysis', {})
        
        # Display sections
        sections = analysis.get('sections', [])
        sections_text = "Song Sections:\n\n"
        for i, section in enumerate(sections, 1):
            name = section.get('name', 'Unknown')
            start = section.get('start', 0)
            end = section.get('end', 0)
            confidence = section.get('confidence', 0)
            
            sections_text += f"{i}. {name}\n"
            sections_text += f"   Time: {self.format_time(start)} - {self.format_time(end)}\n"
            sections_text += f"   Confidence: {confidence:.1%}\n\n"
        
        self.sections_text.setPlainText(sections_text)
        
        # Display analysis details
        details_text = "Analysis Details:\n\n"
        details_text += f"Duration: {self.format_time(analysis.get('duration', 0))}\n"
        details_text += f"Tempo: {analysis.get('tempo', 0):.1f} BPM\n"
        details_text += f"Key: {analysis.get('key', 'Unknown')}\n"
        details_text += f"Beats Detected: {analysis.get('beats_detected', 0)}\n\n"
        
        # Key changes
        key_changes = analysis.get('key_changes', [])
        if key_changes:
            details_text += "Key Changes:\n"
            for change in key_changes:
                timestamp = change.get('timestamp', 0)
                from_key = change.get('from_key', 'Unknown')
                to_key = change.get('to_key', 'Unknown')
                details_text += f"  {self.format_time(timestamp)}: {from_key} → {to_key}\n"
            details_text += "\n"
        
        # Chords
        chords = analysis.get('chords', [])
        if chords:
            details_text += "Chord Progression:\n"
            for chord in chords[:10]:  # Show first 10 chords
                name = chord.get('name', 'Unknown')
                start = chord.get('start', 0)
                end = chord.get('end', 0)
                details_text += f"  {self.format_time(start)}: {name}\n"
            if len(chords) > 10:
                details_text += f"  ... and {len(chords) - 10} more chords\n"
        
        self.details_text.setPlainText(details_text)
        
        # Update timeline
        self.timeline.set_sections(sections)
    
    def format_time(self, seconds: float) -> str:
        """Format time in MM:SS format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def toggle_playback(self):
        """Toggle play/pause."""
        if self.audio_player.is_playing:
            self.audio_player.pause()
            self.play_button.setText("▶ Play")
            self.playback_timer.stop()
        else:
            self.audio_player.play()
            self.play_button.setText("⏸ Pause")
            self.playback_timer.start(100)  # Update every 100ms
    
    def stop_playback(self):
        """Stop playback."""
        self.audio_player.stop()
        self.play_button.setText("▶ Play")
        self.playback_timer.stop()
        self.position_slider.setValue(0)
        self.timeline.set_position(0)
        self.update_time_label()
    
    def seek_to_position(self, timestamp: float):
        """Seek to a specific position."""
        # Note: pygame doesn't support seeking, so this is limited
        # In a production version, we'd use a different audio library
        pass
    
    def slider_pressed(self):
        """Handle slider press (pause updates)."""
        self.playback_timer.stop()
    
    def slider_released(self):
        """Handle slider release (resume updates)."""
        if self.audio_player.is_playing:
            self.playback_timer.start(100)
    
    def update_playback_position(self):
        """Update playback position indicators."""
        # This is a simplified implementation since pygame doesn't provide position
        # In a production version, we'd use a different audio library
        position = self.audio_player.get_position()
        self.position_slider.setValue(int(position))
        self.timeline.set_position(position)
        self.update_time_label()
    
    def update_time_label(self):
        """Update the time display label."""
        current = self.audio_player.get_position()
        total = self.audio_player.get_duration()
        self.time_label.setText(f"{self.format_time(current)} / {self.format_time(total)}")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Sectionist")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Sectionist")
    
    # Create and show main window
    window = SectionistMainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()