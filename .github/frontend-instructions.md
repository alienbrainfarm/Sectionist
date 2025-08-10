---
description: 'Python frontend development for cross-platform GUI with PyQt6'
applyTo: 'frontend/**/*.py'
---

# Sectionist Frontend Development Instructions

## Frontend Architecture

The Sectionist frontend is a cross-platform PyQt6 application that provides a rich GUI for audio analysis. It communicates with the Python backend via HTTP API and includes audio playback, timeline visualization, and interactive editing capabilities.

## Core Technologies

### GUI Framework Stack
- **PyQt6**: Modern Qt6 bindings for Python with cross-platform support
- **python-vlc**: VLC media player bindings for robust audio playback
- **requests**: HTTP client for backend API communication
- **mutagen**: Audio file metadata extraction

### Key GUI Features
- Drag-and-drop audio file support
- Interactive timeline visualization with zoom and scroll
- Audio playback controls with seeking and position tracking
- Real-time analysis progress display
- Cross-platform compatibility (Windows, macOS, Linux)

## PyQt6 Development Patterns

### Application Structure
```python
# Main application setup
app = QApplication(sys.argv)
app.setApplicationName("Sectionist")
app.setApplicationVersion("1.0.0")

# Enable high DPI scaling for modern displays
app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
```

### Threading for Long Operations
```python
class AnalysisWorker(QThread):
    """Worker thread for background audio analysis."""
    
    # Define signals for communication with main thread
    progress_updated = pyqtSignal(int)  # Progress percentage
    analysis_completed = pyqtSignal(dict)  # Analysis results
    analysis_failed = pyqtSignal(str)  # Error message
    
    def __init__(self, audio_file_path: str):
        super().__init__()
        self.audio_file_path = audio_file_path
        
    def run(self):
        """Perform analysis in background thread."""
        try:
            # Send file to backend for analysis
            result = self.send_analysis_request()
            self.analysis_completed.emit(result)
        except Exception as e:
            self.analysis_failed.emit(str(e))
```

### Signal-Slot Connections
```python
# Connect worker signals to main window slots
self.analysis_worker.progress_updated.connect(self.update_progress)
self.analysis_worker.analysis_completed.connect(self.display_results)
self.analysis_worker.analysis_failed.connect(self.show_error)
```

## Audio Playback Implementation

### VLC Integration
```python
class AudioPlayer(QObject):
    """VLC-based audio player with Qt integration."""
    
    position_changed = pyqtSignal(float)  # Current position in seconds
    duration_changed = pyqtSignal(float)  # Total duration in seconds
    
    def __init__(self):
        super().__init__()
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        
        # Set up position tracking
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        self.timer.start(100)  # Update every 100ms
    
    def load_file(self, file_path: str):
        """Load audio file for playback."""
        media = self.vlc_instance.media_new(file_path)
        self.player.set_media(media)
        
    def seek_to_position(self, position: float):
        """Seek to specific position in seconds."""
        if self.player.get_length() > 0:
            relative_pos = position / (self.player.get_length() / 1000)
            self.player.set_position(relative_pos)
```

### Playback Controls
- Implement play/pause/stop functionality
- Provide seeking with sample-accurate positioning
- Display current position and total duration
- Handle various audio formats consistently

## Timeline Visualization

### Custom Qt Widgets
```python
class TimelineWidget(QWidget):
    """Custom widget for timeline visualization and editing."""
    
    section_clicked = pyqtSignal(int)  # Section index
    position_changed = pyqtSignal(float)  # Clicked position in seconds
    
    def __init__(self):
        super().__init__()
        self.sections = []
        self.duration = 0.0
        self.current_position = 0.0
        
        # Enable mouse tracking for interactive features
        self.setMouseTracking(True)
        
    def paintEvent(self, event):
        """Custom painting for timeline visualization."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw timeline background
        self.draw_timeline_background(painter)
        
        # Draw sections with different colors
        self.draw_sections(painter)
        
        # Draw current playback position
        self.draw_playback_cursor(painter)
        
    def mousePressEvent(self, event):
        """Handle mouse clicks for seeking and section selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Convert mouse position to time position
            position = self.pixel_to_time(event.position().x())
            self.position_changed.emit(position)
```

### Zoom and Scroll Support
- Implement smooth zooming with mouse wheel
- Provide horizontal scrolling for long tracks
- Maintain readable section labels at all zoom levels
- Support keyboard shortcuts for navigation

## Drag and Drop Implementation

### File Drop Support
```python
class MainWindow(QMainWindow):
    """Main application window with drag-and-drop support."""
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            # Check if dropped files are audio files
            urls = event.mimeData().urls()
            if self.has_audio_files(urls):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        """Handle file drop events."""
        urls = event.mimeData().urls()
        audio_files = self.filter_audio_files(urls)
        
        if audio_files:
            # Load the first audio file
            self.load_audio_file(audio_files[0].toLocalFile())
            event.acceptProposedAction()
```

### Supported File Types
- Validate audio file extensions (MP3, WAV, AIFF, M4A, FLAC, OGG, AAC)
- Check file sizes and provide appropriate feedback
- Handle multiple file drops gracefully
- Provide visual feedback during drag operations

## API Communication

### HTTP Client Implementation
```python
class BackendClient:
    """Client for communicating with Sectionist backend API."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def analyze_audio_file(self, file_path: str, progress_callback=None) -> dict:
        """Send audio file for analysis."""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = self.session.post(
                    f"{self.base_url}/analyze",
                    files=files,
                    timeout=300  # 5 minute timeout
                )
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            raise BackendConnectionError("Cannot connect to backend server")
        except requests.exceptions.Timeout:
            raise BackendTimeoutError("Analysis request timed out")
        except requests.exceptions.HTTPError as e:
            raise BackendAPIError(f"Backend API error: {e}")
```

### Error Handling
- Implement proper exception handling for network errors
- Provide user-friendly error messages
- Handle backend server unavailability gracefully
- Implement retry logic for transient failures

## User Interface Design

### Layout Management
```python
# Use proper layout managers for responsive design
main_layout = QVBoxLayout()

# Header with controls
header_layout = QHBoxLayout()
header_layout.addWidget(self.play_button)
header_layout.addWidget(self.position_label)
header_layout.addStretch()  # Push elements to left

# Timeline takes main space
main_layout.addWidget(self.timeline_widget, 1)  # Stretch factor 1

# Status bar at bottom
main_layout.addWidget(self.status_bar)

central_widget = QWidget()
central_widget.setLayout(main_layout)
self.setCentralWidget(central_widget)
```

### Responsive Design
- Use proper layout managers instead of fixed positioning
- Implement minimum and maximum window sizes
- Handle high DPI displays correctly
- Provide keyboard shortcuts for all major functions

## Cross-Platform Considerations

### Platform-Specific Code
```python
import platform

def get_default_audio_path():
    """Get platform-appropriate default audio directory."""
    system = platform.system()
    
    if system == "Windows":
        return os.path.join(os.path.expanduser("~"), "Music")
    elif system == "Darwin":  # macOS
        return os.path.join(os.path.expanduser("~"), "Music")
    else:  # Linux and others
        return os.path.join(os.path.expanduser("~"), "Music")
```

### File Path Handling
- Use `pathlib` for cross-platform path operations
- Handle different path separators correctly
- Support Unicode filenames on all platforms
- Implement proper file permission checks

### Audio Codec Support
- Test audio playback on all target platforms
- Handle missing codec situations gracefully
- Provide informative error messages for unsupported formats
- Document platform-specific audio requirements

## Testing Standards

### GUI Testing
```python
import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

def test_file_loading(qtbot, main_window):
    """Test audio file loading functionality."""
    # Add widget to qtbot for automatic cleanup
    qtbot.addWidget(main_window)
    
    # Simulate file drop
    test_file = "test_audio.wav"
    main_window.load_audio_file(test_file)
    
    # Verify UI updates
    assert main_window.file_label.text() == test_file
    assert main_window.timeline_widget.duration > 0
```

### Integration Testing
- Test backend communication with mock servers
- Verify audio playback functionality
- Test timeline visualization with known data
- Test cross-platform file operations

### User Interaction Testing
- Test drag-and-drop functionality
- Verify keyboard shortcuts work correctly
- Test timeline seeking and playback synchronization
- Test error dialog display and handling

## Performance Optimization

### Memory Management
- Properly dispose of Qt objects when no longer needed
- Avoid memory leaks in signal-slot connections
- Use weak references where appropriate
- Monitor memory usage during long sessions

### UI Responsiveness
- Always use background threads for long operations
- Update UI progressively during analysis
- Implement proper progress indicators
- Use efficient painting for timeline widget

### Resource Loading
- Load resources (icons, styles) efficiently
- Use Qt resource system for embedded assets
- Implement lazy loading for large datasets
- Cache frequently accessed data

## Deployment and Distribution

### Package Structure
```
sectionist/
├── main.py              # Application entry point
├── requirements.txt     # Dependencies
├── setup.py            # Installation script
├── resources/          # Icons, styles, etc.
├── sectionist/         # Main package
│   ├── __init__.py
│   ├── main_window.py
│   ├── timeline_widget.py
│   ├── audio_player.py
│   └── analysis_worker.py
└── tests/              # Test suite
```

### Cross-Platform Building
- Use PyInstaller for creating standalone executables
- Configure proper application icons for each platform
- Handle platform-specific dependencies
- Test distribution packages on target platforms

### Application Metadata
- Set proper application name and version
- Include appropriate copyright and license information
- Configure application icons and file associations
- Implement proper application settings storage