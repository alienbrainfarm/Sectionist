#!/usr/bin/env python3
"""
Sectionist - Python Frontend Prototype

A cross-platform audio analysis frontend built with PyQt6 to replace the Swift frontend.
This provides the same functionality as the Swift version but works on Windows, macOS, and Linux.

Features:
- Drag & drop audio file support
- Communication with existing Python backend
- Audio playback controls with seeking and position tracking (VLC-based)
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
        QGridLayout, QSpacerItem, QSizePolicy, QMenuBar, QMenu, QInputDialog
    )
    from PyQt6.QtCore import (
        Qt, QThread, pyqtSignal, QTimer, QMimeData, QUrl
    )
    from PyQt6.QtGui import (
        QFont, QPixmap, QIcon, QDragEnterEvent, QDropEvent, QPalette, QAction
    )
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PyQt6.QtMultimediaWidgets import QVideoWidget
except ImportError:
    print("PyQt6 not found. Install with: pip install PyQt6")
    sys.exit(1)

try:
    import vlc
except ImportError:
    print("python-vlc not found. Install with: pip install python-vlc")
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
    """Audio player using python-vlc for better seeking and position support."""
    
    def __init__(self):
        # Create VLC instance with options for better compatibility
        vlc_args = [
            '--intf', 'dummy',      # No interface
            '--quiet',              # Less verbose output
        ]
        self.vlc_instance = vlc.Instance(vlc_args)
        self.media_player = self.vlc_instance.media_player_new()
        self.is_playing = False
        self.is_paused = False
        self.current_file = None
        self.duration = 0
        self.media = None
        
    def load_file(self, file_path: str) -> bool:
        """Load an audio file."""
        try:
            # Create media object
            self.media = self.vlc_instance.media_new(file_path)
            self.media_player.set_media(self.media)
            self.current_file = file_path
            
            # Parse media to get duration - use synchronous parsing
            self.media.parse_with_options(vlc.MediaParseFlag.local, 5000)  # 5 second timeout
            
            # Get duration in milliseconds, convert to seconds
            duration_ms = self.media.get_duration()
            if duration_ms > 0:
                self.duration = duration_ms / 1000.0
            else:
                # Fallback to mutagen for duration
                try:
                    audio_file = MutagenFile(file_path)
                    if audio_file is not None:
                        self.duration = audio_file.info.length
                    else:
                        self.duration = 0
                except:
                    self.duration = 0
            
            return True
        except Exception as e:
            print(f"Error loading audio file: {e}")
            return False
    
    def play(self):
        """Start or resume playback."""
        if self.current_file:
            if self.is_paused:
                self.media_player.pause()
                self.is_paused = False
            else:
                self.media_player.play()
            self.is_playing = True
    
    def pause(self):
        """Pause playback."""
        if self.is_playing:
            self.media_player.pause()
            self.is_paused = True
            self.is_playing = False
    
    def stop(self):
        """Stop playback."""
        self.media_player.stop()
        self.is_playing = False
        self.is_paused = False
    
    def set_position(self, position: float):
        """Set playback position in seconds."""
        if self.current_file and self.duration > 0:
            # VLC expects position as a ratio between 0.0 and 1.0
            position_ratio = max(0.0, min(1.0, position / self.duration))
            self.media_player.set_position(position_ratio)
    
    def get_position(self) -> float:
        """Get current playback position in seconds."""
        if self.current_file and self.duration > 0:
            # Get position ratio and convert to seconds
            position_ratio = self.media_player.get_position()
            if position_ratio >= 0:  # VLC returns -1 for invalid position
                return position_ratio * self.duration
        return 0.0
    
    def get_duration(self) -> float:
        """Get total duration in seconds."""
        return self.duration


class TimelineWidget(QWidget):
    """Timeline visualization widget."""
    
    section_clicked = pyqtSignal(float)  # Emit timestamp when section is clicked
    section_renamed = pyqtSignal(int, str)  # Emit section index and new name
    section_resized = pyqtSignal(int, float, float)  # Emit section index, new start, new end
    section_separator_moved = pyqtSignal(int, float)  # Emit separator index and new position
    
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
        
        # For section editing
        self.editing_section = -1
        self.resize_mode = None  # 'start', 'end', or None
        self.resize_section = -1
        self.last_click_time = 0
        self.drag_start_x = 0
        self.drag_time_display = ""  # Store current drag time for display
        
        # Define consistent colors for section types
        self.section_colors = {
            'intro': '#4A90E2',      # Blue
            'verse': '#7ED321',      # Green  
            'chorus': '#F5A623',     # Orange
            'bridge': '#BD10E0',     # Purple
            'outro': '#B8E986',      # Light green
            'instrumental': '#50E3C2', # Turquoise
            'solo': '#D0021B',       # Red
            'breakdown': '#9013FE',  # Dark purple
            'interlude': '#F8E71C',  # Yellow
            'pre-chorus': '#FF6B35', # Orange-red
            'post-chorus': '#6C5CE7', # Blue-purple
            'default': '#95A5A6'     # Gray for unknown sections
        }
    
    def get_section_color(self, section_name):
        """Get color for section based on its name."""
        section_name = section_name.lower().strip()
        
        # Check for exact matches first
        if section_name in self.section_colors:
            return self.section_colors[section_name]
        
        # Check for partial matches
        for section_type, color in self.section_colors.items():
            if section_type in section_name:
                return color
        
        # Default color
        return self.section_colors['default']
    
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
            for i, section in enumerate(self.sections):
                start_time = section.get('start', 0)
                end_time = section.get('end', 0)
                name = section.get('name', 'Section')
                
                # Calculate position and width
                x = int((start_time / self.duration) * rect.width())
                width = int(((end_time - start_time) / self.duration) * rect.width())
                
                # Get consistent color based on section type
                color_hex = self.get_section_color(name)
                color = QColor(color_hex)
                painter.fillRect(x, 20, width, rect.height() - 20, color)
                
                # Draw section label with number
                painter.setPen(QPen(QColor(0, 0, 0)))
                if width > 50:  # Only draw text if there's enough space
                    section_text = f"{i + 1}. {name}"
                    painter.drawText(x + 5, 40, section_text)
        
        # Draw time scale at the top
        if self.duration > 0:
            painter.setPen(QPen(QColor(100, 100, 100)))
            # Draw time markers every minute or based on duration
            time_interval = 60  # seconds
            if self.duration < 120:  # Less than 2 minutes
                time_interval = 30
            elif self.duration < 300:  # Less than 5 minutes  
                time_interval = 60
            else:
                time_interval = 120
            
            for t in range(0, int(self.duration) + 1, time_interval):
                x = int((t / self.duration) * rect.width())
                painter.drawLine(x, 0, x, 15)
                
                # Draw time label
                minutes = int(t // 60)
                seconds = int(t % 60)
                time_text = f"{minutes}:{seconds:02d}"
                painter.drawText(x + 2, 12, time_text)
        
        # Draw current position indicator
        if self.duration > 0:
            pos_x = int((self.current_position / self.duration) * rect.width())
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.drawLine(pos_x, 0, pos_x, rect.height())
        
        # Draw drag time display while dragging
        if self.drag_time_display:
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            
            # Draw background rectangle for better visibility
            text_rect = painter.fontMetrics().boundingRect(self.drag_time_display)
            bg_rect = text_rect.adjusted(-5, -2, 5, 2)
            bg_rect.moveTopLeft(rect.topLeft() + painter.fontMetrics().boundingRect("").topLeft())
            bg_rect.moveTop(rect.height() - 25)
            bg_rect.moveLeft(10)
            
            painter.fillRect(bg_rect, QColor(255, 255, 0, 200))  # Semi-transparent yellow
            painter.drawRect(bg_rect)
            painter.drawText(bg_rect.adjusted(5, 2, -5, -2), Qt.AlignmentFlag.AlignCenter, 
                           f"Time: {self.drag_time_display}")
    
    def get_section_at_position(self, x):
        """Get section index at given x position."""
        if not self.sections or self.duration <= 0:
            return -1
        
        timestamp = (x / self.width()) * self.duration
        
        for i, section in enumerate(self.sections):
            start = section.get('start', 0)
            end = section.get('end', 0)
            if start <= timestamp <= end:
                return i
        return -1
    
    def get_resize_mode(self, x, section_idx):
        """Determine if mouse is near section edge for resizing."""
        if section_idx < 0 or section_idx >= len(self.sections):
            return None
        
        section = self.sections[section_idx]
        start_time = section.get('start', 0)
        end_time = section.get('end', 0)
        
        start_x = int((start_time / self.duration) * self.width())
        end_x = int((end_time / self.duration) * self.width())
        
        # Check if near edges (within 5 pixels)
        if abs(x - start_x) <= 5:
            return 'start'
        elif abs(x - end_x) <= 5:
            return 'end'
        return None
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        import time
        
        current_time = time.time()
        x = event.position().x()
        section_idx = self.get_section_at_position(x)
        
        # Check for double-click
        if current_time - self.last_click_time < 0.3 and section_idx >= 0:
            self.start_rename_section(section_idx)
            return
        
        self.last_click_time = current_time
        
        if section_idx >= 0:
            # Check if near section edge for resizing
            resize_mode = self.get_resize_mode(x, section_idx)
            if resize_mode:
                self.resize_mode = resize_mode
                self.resize_section = section_idx
                self.drag_start_x = x
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                # Regular section click
                if self.duration > 0:
                    timestamp = (x / self.width()) * self.duration
                    self.section_clicked.emit(timestamp)
        else:
            # Click outside sections
            if self.duration > 0:
                timestamp = (x / self.width()) * self.duration
                self.section_clicked.emit(timestamp)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        x = event.position().x()
        
        if self.resize_mode and self.resize_section >= 0:
            # Handle section resizing/separator dragging
            timestamp = (x / self.width()) * self.duration
            section = self.sections[self.resize_section]
            
            # Format time for display
            minutes = int(timestamp // 60)
            seconds = int(timestamp % 60)
            milliseconds = int((timestamp % 1) * 1000)
            self.drag_time_display = f"{minutes}:{seconds:02d}.{milliseconds:03d}"
            
            if self.resize_mode == 'start':
                # When dragging the start of a section, we're moving the separator
                # between this section and the previous one
                prev_section_idx = self.resize_section - 1
                if prev_section_idx >= 0:
                    # Constrain the new position
                    prev_section = self.sections[prev_section_idx]
                    min_time = prev_section.get('start', 0) + 1  # Must be after previous section start
                    max_time = section.get('end', 0) - 1  # Must be before current section end
                    new_time = max(min_time, min(timestamp, max_time))
                    
                    # Emit separator moved signal with the boundary index (between sections)
                    self.section_separator_moved.emit(prev_section_idx, new_time)
                else:
                    # First section, just modify its start
                    new_start = max(0, min(timestamp, section.get('end', 0) - 1))
                    self.section_resized.emit(self.resize_section, new_start, section.get('end', 0))
                    
            elif self.resize_mode == 'end':
                # When dragging the end of a section, we're moving the separator
                # between this section and the next one  
                next_section_idx = self.resize_section + 1
                if next_section_idx < len(self.sections):
                    # Constrain the new position
                    next_section = self.sections[next_section_idx]
                    min_time = section.get('start', 0) + 1  # Must be after current section start
                    max_time = next_section.get('end', 0) - 1  # Must be before next section end
                    new_time = max(min_time, min(timestamp, max_time))
                    
                    # Emit separator moved signal with the boundary index (between sections)
                    self.section_separator_moved.emit(self.resize_section, new_time)
                else:
                    # Last section, just modify its end
                    new_end = max(section.get('start', 0) + 1, min(timestamp, self.duration))
                    self.section_resized.emit(self.resize_section, section.get('start', 0), new_end)
            
            # Force repaint to show time display
            self.update()
        else:
            # Clear drag time display when not dragging
            self.drag_time_display = ""
            # Update cursor based on position
            section_idx = self.get_section_at_position(x)
            if section_idx >= 0:
                resize_mode = self.get_resize_mode(x, section_idx)
                if resize_mode:
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                else:
                    self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        self.resize_mode = None
        self.resize_section = -1
        self.drag_time_display = ""  # Clear drag time display
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()  # Repaint to clear the time display
    
    def start_rename_section(self, section_idx):
        """Start renaming a section."""
        if section_idx < 0 or section_idx >= len(self.sections):
            return
        
        from PyQt6.QtWidgets import QInputDialog
        
        current_name = self.sections[section_idx].get('name', 'Section')
        new_name, ok = QInputDialog.getText(
            self, 
            'Rename Section', 
            f'Enter new name for section {section_idx + 1}:',
            text=current_name
        )
        
        if ok and new_name.strip():
            self.section_renamed.emit(section_idx, new_name.strip())


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
        self.setWindowTitle("Sectionist - Audio Analysis Tool")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
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
        
        # Status bar (replace analysis controls)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666;")
        
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.progress_bar)
        status_layout.addWidget(self.status_label, 1)
        
        layout.addLayout(status_layout)
        
        # Timeline and playback controls
        self.timeline_group = QGroupBox("Timeline & Playback")
        timeline_layout = QVBoxLayout(self.timeline_group)
        
        # Timeline widget
        self.timeline = TimelineWidget()
        self.timeline.section_clicked.connect(self.seek_to_position)
        self.timeline.section_renamed.connect(self.rename_section)
        self.timeline.section_resized.connect(self.resize_section)
        self.timeline.section_separator_moved.connect(self.move_section_separator)
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
        self.position_slider.valueChanged.connect(self.slider_value_changed)
        self.position_slider.setEnabled(False)
        self.slider_is_pressed = False
        
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
        
        # No file selected label (replace drop area)
        self.no_file_label = QLabel("No audio file selected. Use File > Open Audio File to get started.")
        self.no_file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_file_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 10px;
                padding: 40px;
                font-size: 16px;
                color: #666;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(self.no_file_label)
        
        # Hide results initially
        self.timeline_group.setVisible(False)
        self.results_splitter.setVisible(False)
    
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Open Audio File...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.browse_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction('Save Song...', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_song)
        save_action.setEnabled(False)
        self.save_action = save_action
        file_menu.addAction(save_action)
        
        load_action = QAction('Load Song...', self)
        load_action.setShortcut('Ctrl+L')
        load_action.triggered.connect(self.load_song)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        # Recent files submenu
        self.recent_menu = file_menu.addMenu('Load Recent Song')
        self.update_recent_menu()
        
        # Actions menu  
        actions_menu = menubar.addMenu('Actions')
        
        analyze_action = QAction('Analyze Audio', self)
        analyze_action.setShortcut('Ctrl+A')
        analyze_action.triggered.connect(self.analyze_audio)
        analyze_action.setEnabled(False)
        self.analyze_action = analyze_action
        actions_menu.addAction(analyze_action)
        
        # Config menu
        config_menu = menubar.addMenu('Config')
        
        self.toggle_sections_action = QAction('Show Song Sections Panel', self)
        self.toggle_sections_action.setCheckable(True)
        self.toggle_sections_action.setChecked(True)
        self.toggle_sections_action.triggered.connect(self.toggle_sections_panel)
        config_menu.addAction(self.toggle_sections_action)
        
        self.toggle_details_action = QAction('Show Analysis Details Panel', self)
        self.toggle_details_action.setCheckable(True)
        self.toggle_details_action.setChecked(True)
        self.toggle_details_action.triggered.connect(self.toggle_details_panel)
        config_menu.addAction(self.toggle_details_action)
    
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
    
    def load_file(self, file_path: str, auto_analyze: bool = True):
        """Load an audio file."""
        self.current_file = file_path
        filename = Path(file_path).name
        
        # Update UI
        self.file_label.setText(filename)
        self.file_label.setStyleSheet("QLabel { color: black; font-weight: bold; }")
        self.analyze_action.setEnabled(True)
        self.save_action.setEnabled(False)  # Enable after analysis
        self.clear_button.setEnabled(True)
        self.no_file_label.setVisible(False)
        
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
        
        # Auto-analyze audio when file is first opened (unless loading saved data)
        if auto_analyze:
            self.analyze_audio()
    
    def clear_file(self):
        """Clear the current file."""
        self.current_file = None
        self.analysis_results = None
        
        # Stop playback
        self.stop_playback()
        
        # Reset UI
        self.file_label.setText("No file selected")
        self.file_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        self.analyze_action.setEnabled(False)
        self.save_action.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.position_slider.setEnabled(False)
        
        # Clear results
        self.sections_text.clear()
        self.details_text.clear()
        
        # Hide groups and show no file area
        self.timeline_group.setVisible(False)
        self.results_splitter.setVisible(False)
        self.no_file_label.setVisible(True)
    
    def analyze_audio(self):
        """Start audio analysis."""
        if not self.current_file:
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.analyze_action.setEnabled(False)
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
        self.analyze_action.setEnabled(True)
        self.save_action.setEnabled(True)  # Enable save after analysis
        self.status_label.setText("Analysis completed!")
        
        # Show results
        self.display_results(results)
        self.results_splitter.setVisible(True)
        
        # Add to recent files
        if self.current_file:
            self.add_to_recent_files(self.current_file)
    
    def analysis_error(self, error_message: str):
        """Handle analysis error."""
        # Hide progress
        self.progress_bar.setVisible(False)
        self.analyze_action.setEnabled(True)
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
        self.audio_player.set_position(timestamp)
        self.update_playback_position()
    
    def slider_pressed(self):
        """Handle slider press (pause updates)."""
        self.slider_is_pressed = True
        self.playback_timer.stop()
    
    def slider_released(self):
        """Handle slider release (resume updates)."""
        self.slider_is_pressed = False
        if self.audio_player.is_playing:
            self.playback_timer.start(100)
    
    def slider_value_changed(self, value):
        """Handle slider value change (seeking)."""
        if self.slider_is_pressed:  # Only seek when user is dragging
            timestamp = float(value)
            self.audio_player.set_position(timestamp)
            self.timeline.set_position(timestamp)
            self.update_time_label()
    
    def update_playback_position(self):
        """Update playback position indicators."""
        if not self.slider_is_pressed:  # Only update if user is not dragging slider
            position = self.audio_player.get_position()
            self.position_slider.setValue(int(position))
            self.timeline.set_position(position)
        self.update_time_label()
    
    def update_time_label(self):
        """Update the time display label."""
        current = self.audio_player.get_position()
        total = self.audio_player.get_duration()
        self.time_label.setText(f"{self.format_time(current)} / {self.format_time(total)}")
    
    def save_song(self):
        """Save the current song and analysis data."""
        if not self.current_file or not self.analysis_results:
            QMessageBox.warning(self, "Save Song", "No analysis data to save. Please analyze an audio file first.")
            return
        
        folder = QFileDialog.getExistingDirectory(
            self, "Save Song", "", QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            try:
                import shutil
                import json
                
                # Create song folder structure
                song_name = Path(self.current_file).stem
                song_folder = Path(folder) / song_name
                song_folder.mkdir(exist_ok=True)
                
                # Copy audio file
                audio_dest = song_folder / Path(self.current_file).name
                shutil.copy2(self.current_file, audio_dest)
                
                # Save analysis data
                analysis_file = song_folder / "analysis.json"
                with open(analysis_file, 'w') as f:
                    json.dump(self.analysis_results, f, indent=2)
                
                QMessageBox.information(self, "Save Song", f"Song saved successfully to:\n{song_folder}")
                
            except Exception as e:
                QMessageBox.critical(self, "Save Song", f"Failed to save song:\n{str(e)}")
    
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
            import json
            
            folder_path = Path(folder)
            analysis_file = folder_path / "analysis.json"
            
            if not analysis_file.exists():
                QMessageBox.warning(self, "Load Song", "No analysis data found in selected folder.")
                return
            
            # Find audio file
            audio_extensions = {'.mp3', '.wav', '.aiff', '.aif', '.m4a', '.flac', '.ogg', '.aac'}
            audio_files = [f for f in folder_path.iterdir() if f.suffix.lower() in audio_extensions]
            
            if not audio_files:
                QMessageBox.warning(self, "Load Song", "No audio file found in selected folder.")
                return
            
            # Load analysis data
            with open(analysis_file, 'r') as f:
                self.analysis_results = json.load(f)
            
            # Load audio file without auto-analyzing
            self.load_file(str(audio_files[0]), auto_analyze=False)
            
            # Display results without re-analyzing
            self.display_results(self.analysis_results)
            self.results_splitter.setVisible(True)
            self.save_action.setEnabled(True)
            
            QMessageBox.information(self, "Load Song", "Song loaded successfully!")
            
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
        
        if not self.recent_files:
            action = QAction("No recent files", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
            return
        
        for file_path in self.recent_files:
            if Path(file_path).exists():
                filename = Path(file_path).name
                action = QAction(filename, self)
                action.triggered.connect(lambda checked, fp=file_path: self.load_file(fp))
                self.recent_menu.addAction(action)
    
    def save_recent_files(self):
        """Save recent files list to disk."""
        try:
            import json
            recent_file = Path.home() / ".sectionist_recent.json"
            with open(recent_file, 'w') as f:
                json.dump(self.recent_files, f)
        except Exception:
            pass  # Silently fail if can't save recent files
    
    def load_recent_files(self):
        """Load recent files list from disk."""
        try:
            import json
            recent_file = Path.home() / ".sectionist_recent.json"
            if recent_file.exists():
                with open(recent_file, 'r') as f:
                    self.recent_files = json.load(f)
                self.update_recent_menu()
        except Exception:
            pass  # Silently fail if can't load recent files
    
    def toggle_sections_panel(self):
        """Toggle visibility of sections panel."""
        visible = self.sections_group.isVisible()
        self.sections_group.setVisible(not visible)
        self.toggle_sections_action.setText("Show Song Sections Panel" if not visible else "Hide Song Sections Panel")
    
    def toggle_details_panel(self):
        """Toggle visibility of details panel."""
        visible = self.details_group.isVisible()
        self.details_group.setVisible(not visible)
        self.toggle_details_action.setText("Show Analysis Details Panel" if not visible else "Hide Analysis Details Panel")
    
    def rename_section(self, section_idx, new_name):
        """Rename a section."""
        if not self.analysis_results or section_idx < 0:
            return
        
        sections = self.analysis_results.get('analysis', {}).get('sections', [])
        if section_idx < len(sections):
            sections[section_idx]['name'] = new_name
            
            # Update displays
            self.display_results(self.analysis_results)
            self.timeline.set_sections(sections)
            
            # Mark as modified (could save automatically or flag for save)
            self.status_label.setText(f"Section {section_idx + 1} renamed to '{new_name}'")
    
    def resize_section(self, section_idx, new_start, new_end):
        """Resize a section."""
        if not self.analysis_results or section_idx < 0:
            return
        
        sections = self.analysis_results.get('analysis', {}).get('sections', [])
        if section_idx < len(sections):
            sections[section_idx]['start'] = new_start
            sections[section_idx]['end'] = new_end
            
            # Update displays
            self.display_results(self.analysis_results)
            self.timeline.set_sections(sections)
            
            # Mark as modified
            self.status_label.setText(f"Section {section_idx + 1} resized")
    
    def move_section_separator(self, separator_idx, new_time):
        """Move a section separator, affecting both adjacent sections."""
        if not self.analysis_results or separator_idx < 0:
            return
        
        sections = self.analysis_results.get('analysis', {}).get('sections', [])
        if separator_idx < len(sections) - 1:  # Ensure there's a next section
            # Update the end of the current section and start of the next section
            sections[separator_idx]['end'] = new_time
            sections[separator_idx + 1]['start'] = new_time
            
            # Update displays
            self.display_results(self.analysis_results)
            self.timeline.set_sections(sections)
            
            # Mark as modified
            self.status_label.setText(f"Separator between sections {separator_idx + 1} and {separator_idx + 2} moved")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Sectionist")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Sectionist")
    
    # Create and show main window
    window = SectionistMainWindow()
    window.load_recent_files()  # Load recent files on startup
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()