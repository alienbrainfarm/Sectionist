#!/usr/bin/env python3
"""
Sectionist Frontend Package

This package contains the PyQt6-based frontend for Sectionist.
The frontend has been modularized for better maintainability:

- analysis_worker.py - Background analysis worker thread
- audio_player.py - VLC-based audio playback functionality
- timeline_widget.py - Timeline visualization and section editing
- main_window.py - Main application window and UI logic
- sectionist_gui.py - Main entry point and application launcher
"""

# Main classes for external use
from .analysis_worker import AnalysisWorker
from .audio_player import AudioPlayer
from .timeline_widget import TimelineWidget
from .main_window import SectionistMainWindow

__all__ = [
    'AnalysisWorker',
    'AudioPlayer', 
    'TimelineWidget',
    'SectionistMainWindow'
]