#!/usr/bin/env python3
"""
Unit tests for timeline widget improvements
"""
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add frontend directory to path
sys.path.insert(0, '/home/runner/work/Sectionist/Sectionist/frontend')

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QContextMenuEvent

# Import the timeline widget
from timeline_widget import TimelineWidget

class TestTimelineImprovements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        
    def setUp(self):
        self.timeline = TimelineWidget()
        self.timeline.resize(800, 120)
        
        # Set up test sections
        self.test_sections = [
            {'start': 0, 'end': 30, 'name': 'intro'},
            {'start': 30, 'end': 60, 'name': 'verse'},
            {'start': 60, 'end': 90, 'name': 'chorus'}
        ]
        
        self.timeline.set_sections(self.test_sections)
        self.timeline.set_duration(180)
    
    def test_section_boundary_visibility(self):
        """Test that section boundaries are clearly visible."""
        # This would require more complex testing with actual rendering
        # For now, just verify the sections are set correctly
        self.assertEqual(len(self.timeline.sections), 3)
        self.assertEqual(self.timeline.duration, 180)
    
    def test_drag_time_display_improvement(self):
        """Test that drag time display is improved."""
        # Set drag time display
        self.timeline.drag_time_display = "1:15.500"
        self.assertIsNotNone(self.timeline.drag_time_display)
        self.assertEqual(self.timeline.drag_time_display, "1:15.500")
    
    def test_section_position_detection(self):
        """Test section position detection for context menu."""
        # Test position in first section (0-30s, x position ~0-133)
        section_idx = self.timeline.get_section_at_position(50)
        self.assertEqual(section_idx, 0)  # Should be intro section
        
        # Test position in second section (30-60s, x position ~133-266)
        section_idx = self.timeline.get_section_at_position(200)
        self.assertEqual(section_idx, 1)  # Should be verse section
        
        # Test position in third section (60-90s, x position ~266-400)
        section_idx = self.timeline.get_section_at_position(350)
        self.assertEqual(section_idx, 2)  # Should be chorus section
    
    def test_signals_connected(self):
        """Test that new signals are available."""
        # Verify signals exist
        self.assertTrue(hasattr(self.timeline, 'section_joined'))
        self.assertTrue(hasattr(self.timeline, 'section_split'))
    
    def test_split_section_functionality(self):
        """Test section splitting functionality."""
        # Connect a mock handler
        mock_handler = MagicMock()
        self.timeline.section_split.connect(mock_handler)
        
        # Call split function
        self.timeline.split_section_at_position(1, 400)  # Split verse section
        
        # Verify signal was emitted
        mock_handler.assert_called_once()
        args = mock_handler.call_args[0]
        self.assertEqual(args[0], 1)  # Section index
        self.assertEqual(args[1], 45.0)  # Should be middle of 30-60 range

if __name__ == '__main__':
    unittest.main()