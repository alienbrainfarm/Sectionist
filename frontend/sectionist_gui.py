#!/usr/bin/env python3
"""
Sectionist - Python Frontend

A cross-platform audio analysis frontend built with PyQt6, running on
Windows, macOS, and Linux.

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

import signal
import sys

# Check for required dependencies
try:
    from PyQt6.QtWidgets import QApplication
except ImportError:
    print("PyQt6 not found. Install with: pip install PyQt6")
    sys.exit(1)

try:
    import vlc  # noqa: F401  (presence check for a clean error message)
except ImportError:
    print("python-vlc not found. Install with: pip install python-vlc")
    sys.exit(1)

try:
    from mutagen import File as MutagenFile  # noqa: F401  (presence check)
except ImportError:
    print("mutagen not found. Install with: pip install mutagen")
    sys.exit(1)

try:
    import requests  # noqa: F401  (presence check)
except ImportError:
    print("requests not found. Install with: pip install requests")
    sys.exit(1)

# Import main application components
try:
    # Try relative imports first (when run as module)
    from .main_window import SectionistMainWindow
except ImportError:
    # Fall back to absolute imports (when run directly)
    from main_window import SectionistMainWindow


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)

    # Qt runs its own event loop in C++, which never returns control to the
    # interpreter, so Python never gets a chance to raise KeyboardInterrupt and
    # Ctrl-C appears to do nothing. A signal handler plus a periodic no-op
    # timer gives the interpreter a chance to run it.
    signal.signal(signal.SIGINT, lambda *_: app.quit())

    from PyQt6.QtCore import QTimer

    heartbeat = QTimer()
    heartbeat.start(200)
    heartbeat.timeout.connect(lambda: None)

    # Set application properties
    app.setApplicationName("Sectionist")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Sectionist")

    # Create and show main window
    window = SectionistMainWindow()
    window.load_recent_files()  # Load recent files on startup
    window.show()

    # Release playback and worker threads before the process exits, otherwise
    # VLC's threads can keep it alive after the window closes.
    app.aboutToQuit.connect(window.shutdown)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
