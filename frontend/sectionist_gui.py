#!/usr/bin/env python3
"""
Sectionist - Python Frontend

A cross-platform audio analysis frontend built with PyQt6 to replace the Swift frontend.
This provides the same functionality as the Swift version but works on Windows, macOS, and Linux.

Features:
- Drag & drop audio file support
- Communication with existing Python backend
- Audio playback controls with seeking and position tracking (VLC-based)
- Timeline visualization
- Analysis results display
- Cross-platform compatibility

This is the main entry point. The functionality has been split into separate modules:
- analysis_worker.py - Background analysis communication
- audio_player.py - VLC-based audio playback
- timeline_widget.py - Timeline visualization and editing
- main_window.py - Main application window and UI logic
"""

import sys

# Check for required dependencies
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
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

try:
    import requests
except ImportError:
    print("requests not found. Install with: pip install requests")
    sys.exit(1)

# Import main application components
try:
    # Try relative imports first (when run as module)
    from .main_window import SectionistMainWindow
    from .analysis_worker import AnalysisWorker
    from .audio_player import AudioPlayer
    from .timeline_widget import TimelineWidget
except ImportError:
    # Fall back to absolute imports (when run directly)
    from main_window import SectionistMainWindow
    from analysis_worker import AnalysisWorker
    from audio_player import AudioPlayer
    from timeline_widget import TimelineWidget


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