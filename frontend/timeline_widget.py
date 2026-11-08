#!/usr/bin/env python3
"""
Timeline Widget Module for Sectionist GUI

This module contains the TimelineWidget class that provides
timeline visualization and section editing functionality.
"""

from typing import List, Dict
from PyQt6.QtWidgets import QWidget, QInputDialog, QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QAction

try:
    # Package import (frontend/__init__.py imports this module eagerly).
    from .chord_track import (
        CHORD_LANE_HEIGHT,
        chord_at_position,
        chord_boundary_at,
        paint_chord_track,
    )
except ImportError:
    # Direct import when the frontend directory is on sys.path.
    from chord_track import (
        CHORD_LANE_HEIGHT,
        chord_at_position,
        chord_boundary_at,
        paint_chord_track,
    )


class TimelineWidget(QWidget):
    """Timeline visualization widget."""

    section_clicked = pyqtSignal(float)  # Emit timestamp when section is clicked
    section_renamed = pyqtSignal(int, str)  # Emit section index and new name
    section_resized = pyqtSignal(
        int, float, float
    )  # Emit section index, new start, new end
    section_separator_moved = pyqtSignal(
        int, float
    )  # Emit separator index and new position
    section_joined = pyqtSignal(int)  # Emit section index to join with next section
    section_split = pyqtSignal(int, float)  # Emit section index and split position
    chord_renamed = pyqtSignal(int, str)  # Emit chord index and new name
    chord_boundary_moved = pyqtSignal(int, float)  # Emit boundary index and time

    def __init__(self):
        super().__init__()
        self.sections = []
        self.chords = []
        self.downbeats = []
        self.duration = 0
        self.current_position = 0
        self.setMinimumHeight(130)
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

        # For chord editing
        self.selected_chord = -1
        self.chord_resize = -1
        self.last_chord_click_time = 0.0

        # Define consistent colors for section types
        self.section_colors = {
            "intro": "#4A90E2",  # Blue
            "verse": "#7ED321",  # Green
            "chorus": "#F5A623",  # Orange
            "bridge": "#BD10E0",  # Purple
            "outro": "#B8E986",  # Light green
            "instrumental": "#50E3C2",  # Turquoise
            "solo": "#D0021B",  # Red
            "breakdown": "#9013FE",  # Dark purple
            "interlude": "#F8E71C",  # Yellow
            "pre-chorus": "#FF6B35",  # Orange-red
            "post-chorus": "#6C5CE7",  # Blue-purple
            "default": "#95A5A6",  # Gray for unknown sections
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
        return self.section_colors["default"]

    def set_sections(self, sections: List[Dict]):
        """Set the song sections to display."""
        self.sections = sections
        self.update()

    def set_downbeats(self, downbeats: List[float]):
        """Set the bar lines drawn behind the sections."""
        self.downbeats = list(downbeats or [])
        self.update()

    def set_chords(self, chords: List[Dict]):
        """Set the chord track drawn under the sections."""
        self.chords = chords or []
        self.selected_chord = -1
        self.chord_resize = -1
        self.update()

    # --- chord track geometry and editing ---------------------------------

    def chord_lane_top(self):
        """Y coordinate where the chord track starts."""
        if not self.chords:
            return self.height()
        return self.height() - CHORD_LANE_HEIGHT

    def is_in_chord_lane(self, y):
        return bool(self.chords) and y >= self.chord_lane_top()

    def get_chord_at_position(self, x):
        """Index of the chord under ``x``, or -1."""
        return chord_at_position(self.chords, self.duration, self.width(), x)

    def get_chord_boundary(self, x, tolerance=6):
        """Index of the boundary between chord ``i`` and ``i+1`` near ``x``."""
        return chord_boundary_at(self.chords, self.duration, self.width(), x, tolerance)

    def _format_drag_time(self, timestamp):
        minutes = int(timestamp // 60)
        seconds = int(timestamp % 60)
        milliseconds = int((timestamp % 1) * 1000)
        return f"{minutes}:{seconds:02d}.{milliseconds:03d}"

    def handle_chord_press(self, x, current_time):
        """Select, rename or start dragging a chord boundary."""
        index = self.get_chord_at_position(x)
        if index < 0:
            return

        if current_time - self.last_chord_click_time < 0.3:
            self.start_rename_chord(index)
            return
        self.last_chord_click_time = current_time

        boundary = self.get_chord_boundary(x)
        if boundary >= 0:
            self.chord_resize = boundary
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.selected_chord = index
            self.update()

    def drag_chord_boundary(self, x):
        """Move the boundary between two chords, clamped to their span."""
        index = self.chord_resize
        if index < 0 or index + 1 >= len(self.chords):
            return

        left = self.chords[index]
        right = self.chords[index + 1]
        timestamp = (x / self.width()) * self.duration
        lower = float(left.get("start", 0)) + 0.05
        upper = float(right.get("end", 0)) - 0.05
        if upper <= lower:
            return

        new_time = max(lower, min(timestamp, upper))
        self.drag_time_display = self._format_drag_time(new_time)
        self.chord_boundary_moved.emit(index, new_time)
        self.update()

    def start_rename_chord(self, chord_idx):
        """Ask for a new chord name and emit the change."""
        if chord_idx < 0 or chord_idx >= len(self.chords):
            return
        current = str(self.chords[chord_idx].get("name", ""))
        name, ok = QInputDialog.getText(
            self, "Rename Chord", "Chord name:", text=current
        )
        if ok and name.strip():
            self.chord_renamed.emit(chord_idx, name.strip())

    def show_chord_menu(self, event):
        """Context menu for a chord block."""
        index = self.get_chord_at_position(event.pos().x())
        if index < 0:
            return
        name = self.chords[index].get("name", "")
        menu = QMenu(self)
        rename_action = QAction(f"Rename '{name}'", self)
        rename_action.triggered.connect(lambda: self.start_rename_chord(index))
        menu.addAction(rename_action)
        menu.exec(event.globalPos())

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
        painter = QPainter(self)
        rect = self.rect()

        # Background
        painter.fillRect(rect, QColor(240, 240, 240))

        chord_lane = rect.height() - CHORD_LANE_HEIGHT if self.chords else rect.height()
        section_bottom = chord_lane - (6 if self.chords else 0)

        if self.duration > 0 and self.sections:
            # Draw sections
            for i, section in enumerate(self.sections):
                start_time = section.get("start", 0)
                end_time = section.get("end", 0)
                name = section.get("name", "Section")

                # Calculate position and width
                x = int((start_time / self.duration) * rect.width())
                width = int(((end_time - start_time) / self.duration) * rect.width())

                # Get consistent color based on section type
                color_hex = self.get_section_color(name)
                color = QColor(color_hex)
                painter.fillRect(x, 20, width, section_bottom - 20, color)

                # Draw clear section boundaries with strong borders
                border_pen = QPen(QColor(0, 0, 0), 2)  # Black border, 2px thick
                painter.setPen(border_pen)
                painter.drawRect(x, 20, width, section_bottom - 20)

                # Draw section separators between sections (more visible)
                if i < len(self.sections) - 1:  # Not the last section
                    separator_x = int((end_time / self.duration) * rect.width())
                    # Draw a thicker separator line
                    separator_pen = QPen(QColor(0, 0, 0), 3)  # Thick black line
                    painter.setPen(separator_pen)
                    painter.drawLine(separator_x, 20, separator_x, section_bottom)

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

        # Draw bar lines across the section area, skipping ones too close
        # together to be legible.
        if self.duration > 0 and self.downbeats and section_bottom > 20:
            painter.setPen(QPen(QColor(0, 0, 0, 45), 1))
            previous_x = None
            for beat in self.downbeats:
                if beat <= 0 or beat >= self.duration:
                    continue
                x = int((beat / self.duration) * rect.width())
                if previous_x is not None and x - previous_x < 3:
                    continue
                painter.drawLine(x, 20, x, section_bottom)
                previous_x = x

        # Draw the chord track beneath the sections
        if self.duration > 0 and self.chords:
            paint_chord_track(
                painter,
                self.chords,
                self.duration,
                rect.width(),
                rect.height(),
                self.selected_chord,
            )

        # Draw current position indicator
        if self.duration > 0:
            pos_x = int((self.current_position / self.duration) * rect.width())
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.drawLine(pos_x, 0, pos_x, rect.height())

        # Draw drag time display while dragging (improved visibility)
        if self.drag_time_display:
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))  # Larger font

            # Calculate better position and size for time display
            text_rect = painter.fontMetrics().boundingRect(self.drag_time_display)
            # Make background significantly larger for better visibility
            bg_rect = text_rect.adjusted(-15, -8, 15, 8)

            # Position in center-top area for better visibility
            bg_rect.moveTopLeft(rect.topLeft())
            bg_rect.moveTop(25)  # Below time scale
            bg_rect.moveLeft(
                (rect.width() - bg_rect.width()) // 2
            )  # Center horizontally

            # Draw with better contrast and visibility
            painter.fillRect(
                bg_rect, QColor(255, 255, 0, 240)
            )  # Brighter yellow with more opacity
            painter.setPen(QPen(QColor(0, 0, 0), 2))  # Thicker border
            painter.drawRect(bg_rect)

            # Draw time text with better contrast
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(
                bg_rect, Qt.AlignmentFlag.AlignCenter, self.drag_time_display
            )

    def get_section_at_position(self, x):
        """Get section index at given x position."""
        if not self.sections or self.duration <= 0:
            return -1

        timestamp = (x / self.width()) * self.duration

        for i, section in enumerate(self.sections):
            start = section.get("start", 0)
            end = section.get("end", 0)
            if start <= timestamp <= end:
                return i
        return -1

    def get_resize_mode(self, x, section_idx):
        """Determine if mouse is near section edge for resizing."""
        if section_idx < 0 or section_idx >= len(self.sections):
            return None

        section = self.sections[section_idx]
        start_time = section.get("start", 0)
        end_time = section.get("end", 0)

        start_x = int((start_time / self.duration) * self.width())
        end_x = int((end_time / self.duration) * self.width())

        # Check if near edges (within 5 pixels)
        if abs(x - start_x) <= 5:
            return "start"
        elif abs(x - end_x) <= 5:
            return "end"
        return None

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        import time

        current_time = time.time()
        x = event.position().x()
        y = event.position().y()

        if self.is_in_chord_lane(y):
            self.handle_chord_press(x, current_time)
            return

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

        # Once a chord boundary drag starts it continues even if the pointer
        # strays out of the lane, matching how section resizing behaves.
        if self.chord_resize >= 0:
            self.drag_chord_boundary(x)
            return

        if self.resize_mode and self.resize_section >= 0:
            # Handle section resizing/separator dragging
            timestamp = (x / self.width()) * self.duration
            section = self.sections[self.resize_section]

            # Format time for display
            minutes = int(timestamp // 60)
            seconds = int(timestamp % 60)
            milliseconds = int((timestamp % 1) * 1000)
            self.drag_time_display = f"{minutes}:{seconds:02d}.{milliseconds:03d}"

            if self.resize_mode == "start":
                # When dragging the start of a section, we're moving the separator
                # between this section and the previous one
                prev_section_idx = self.resize_section - 1
                if prev_section_idx >= 0:
                    # Constrain the new position
                    prev_section = self.sections[prev_section_idx]
                    min_time = (
                        prev_section.get("start", 0) + 1
                    )  # Must be after previous section start
                    max_time = (
                        section.get("end", 0) - 1
                    )  # must end before this section does
                    new_time = max(min_time, min(timestamp, max_time))

                    # Emit the boundary index between the two sections
                    self.section_separator_moved.emit(prev_section_idx, new_time)
                else:
                    # First section, just modify its start
                    new_start = max(0, min(timestamp, section.get("end", 0) - 1))
                    self.section_resized.emit(
                        self.resize_section, new_start, section.get("end", 0)
                    )

            elif self.resize_mode == "end":
                # When dragging the end of a section, we're moving the separator
                # between this section and the next one
                next_section_idx = self.resize_section + 1
                if next_section_idx < len(self.sections):
                    # Constrain the new position
                    next_section = self.sections[next_section_idx]
                    min_time = (
                        section.get("start", 0) + 1
                    )  # Must be after current section start
                    max_time = (
                        next_section.get("end", 0) - 1
                    )  # must end before the next section
                    new_time = max(min_time, min(timestamp, max_time))

                    # Emit the boundary index between the two sections
                    self.section_separator_moved.emit(self.resize_section, new_time)
                else:
                    # Last section, just modify its end
                    new_end = max(
                        section.get("start", 0) + 1, min(timestamp, self.duration)
                    )
                    self.section_resized.emit(
                        self.resize_section, section.get("start", 0), new_end
                    )

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
        self.chord_resize = -1
        self.resize_mode = None
        self.resize_section = -1
        self.drag_time_display = ""  # Clear drag time display
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()  # Repaint to clear the time display

    def start_rename_section(self, section_idx):
        """Start renaming a section."""
        if section_idx < 0 or section_idx >= len(self.sections):
            return

        current_name = self.sections[section_idx].get("name", "Section")
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Section",
            f"Enter new name for section {section_idx + 1}:",
            text=current_name,
        )

        if ok and new_name.strip():
            self.section_renamed.emit(section_idx, new_name.strip())

    def contextMenuEvent(self, event):
        """Handle right-click context menu."""
        if self.is_in_chord_lane(event.pos().y()):
            self.show_chord_menu(event)
            return

        x = event.x()
        section_idx = self.get_section_at_position(x)

        if section_idx >= 0:
            # Create context menu for the section
            menu = QMenu(self)

            # Rename action
            rename_action = QAction(f"Rename Section {section_idx + 1}", self)
            rename_action.triggered.connect(
                lambda: self.start_rename_section(section_idx)
            )
            menu.addAction(rename_action)

            menu.addSeparator()

            # Join with next section (if not the last section)
            if section_idx < len(self.sections) - 1:
                join_action = QAction("Join with Next Section", self)
                join_action.triggered.connect(
                    lambda: self.section_joined.emit(section_idx)
                )
                menu.addAction(join_action)

            # Split section action
            split_action = QAction("Split Section in Half", self)
            split_action.triggered.connect(
                lambda: self.split_section_at_position(section_idx, x)
            )
            menu.addAction(split_action)

            # Show context menu
            menu.exec(event.globalPos())

    def split_section_at_position(self, section_idx, x_position):
        """Split a section at the given x position (middle if x_position is None)."""
        if section_idx < 0 or section_idx >= len(self.sections):
            return

        section = self.sections[section_idx]
        start_time = section.get("start", 0)
        end_time = section.get("end", 0)

        # Calculate split position (at the middle of the section)
        split_time = (start_time + end_time) / 2.0

        # Emit signal for splitting
        self.section_split.emit(section_idx, split_time)
