#!/usr/bin/env python3
"""
Timeline Widget Module for Sectionist GUI

This module contains the TimelineWidget class that provides
timeline visualization and section editing functionality.
"""

from typing import List, Dict
from PyQt6.QtWidgets import QWidget, QInputDialog, QMenu, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QAction

try:
    # Package import (frontend/__init__.py imports this module eagerly).
    from .chord_track import (
        CHORD_LANE_HEIGHT,
        chord_at_position,
        chord_boundary_at,
        paint_chord_track,
    )
    from . import timeline_paint as paint
    from .cycle import CycleDrag, CycleRegion, hit_test, paint_cycle
    from .theme import section_color
except ImportError:
    # Direct import when the frontend directory is on sys.path.
    from chord_track import (
        CHORD_LANE_HEIGHT,
        chord_at_position,
        chord_boundary_at,
        paint_chord_track,
    )
    import timeline_paint as paint
    from cycle import CycleDrag, CycleRegion, hit_test, paint_cycle
    from theme import section_color


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
    position_changed = pyqtSignal(float)  # playhead moved (playback or seek)
    cycle_changed = pyqtSignal(object)  # CycleRegion, or None

    def __init__(self):
        super().__init__()
        self.sections = []
        self.chords = []
        self.downbeats = []
        self.duration = 0
        self.current_position = 0
        self.setMinimumHeight(170)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)  # hover feedback and resize cursors
        self.hover_section = -1
        self.drag_x = 0.0
        # Shown when there is a duration but no sections yet.
        self.placeholder_text = ""
        self.cycle = None  # CycleRegion drawn in the ruler
        self.cycle_drag = CycleDrag()

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

    def get_section_color(self, section_name):
        """Get color for section based on its name."""
        return section_color(section_name)

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
        self.drag_x = x
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
        self.position_changed.emit(position)

    def current_section(self):
        """Index of the section containing the playhead, or -1."""
        for index, section in enumerate(self.sections):
            if section.get("start", 0) <= self.current_position < section.get("end", 0):
                return index
        return -1

    def paintEvent(self, event):
        """Paint the timeline."""
        painter = QPainter(self)
        rect = self.rect()
        width = rect.width()
        paint.paint_background(painter, rect)

        if self.chords:
            section_bottom = rect.height() - CHORD_LANE_HEIGHT - paint.CHORD_GAP
        else:
            section_bottom = rect.height() - 4

        if self.duration <= 0:
            paint.paint_placeholder(
                painter, rect, self.placeholder_text or "No song loaded"
            )
            return

        paint.paint_ruler(painter, self.duration, width)

        if self.sections:
            paint.paint_sections(
                painter,
                self.sections,
                self.duration,
                width,
                section_bottom,
                downbeats=self.downbeats,
                current=self.current_section(),
                hovered=self.hover_section,
            )
        elif self.placeholder_text:
            band = rect.adjusted(0, paint.SECTION_TOP, 0, 0)
            paint.paint_placeholder(painter, band, self.placeholder_text)

        if self.chords:
            paint_chord_track(
                painter,
                self.chords,
                self.duration,
                width,
                rect.height(),
                self.selected_chord,
            )

        paint_cycle(
            painter, self.cycle, self.duration, width, paint.RULER_HEIGHT, rect.height()
        )
        paint.paint_playhead(
            painter, self.current_position, self.duration, width, rect.height()
        )
        paint.paint_drag_bubble(painter, self.drag_time_display, self.drag_x, width)

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

        if y < paint.RULER_HEIGHT and self.duration > 0:
            seconds = x / self.width() * self.duration
            self.cycle_drag.press(self.cycle, seconds, x, self.duration, self.width())
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

        if self.cycle_drag.active or event.position().y() < paint.RULER_HEIGHT:
            self.cycle_hover_or_drag(event, x)
            return

        if self.resize_mode and self.resize_section >= 0:
            # Handle section resizing/separator dragging
            timestamp = (x / self.width()) * self.duration
            section = self.sections[self.resize_section]
            self.drag_x = x
            self.drag_time_display = self._format_drag_time(timestamp)

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
            # Update hover highlight and cursor based on position
            in_chords = self.is_in_chord_lane(event.position().y())
            section_idx = -1 if in_chords else self.get_section_at_position(x)
            if section_idx != self.hover_section:
                self.hover_section = section_idx
                self.update()
            if section_idx >= 0:
                resize_mode = self.get_resize_mode(x, section_idx)
                if resize_mode:
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                else:
                    self.setCursor(Qt.CursorShape.PointingHandCursor)
            elif in_chords and self.get_chord_boundary(x) >= 0:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif in_chords:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def cycle_hover_or_drag(self, event, x):
        """Preview a cycle drag, or show which part of the region is under x."""
        seconds = x / max(self.width(), 1) * self.duration
        if self.cycle_drag.active:
            free = bool(event.modifiers() & Qt.KeyboardModifier.AltModifier)
            region = self.cycle_drag.move(
                seconds, self.downbeats, self.duration, self.width(), free
            )
            self.cycle = region
            if region is not None and self.cycle_drag.moved:
                self.drag_x = x
                self.drag_time_display = (
                    f"{self._format_drag_time(region.start)} - "
                    f"{self._format_drag_time(region.end)}"
                )
            self.update()
            return
        part = hit_test(self.cycle, x, self.duration, self.width())
        cursor = {
            "start": Qt.CursorShape.SizeHorCursor,
            "end": Qt.CursorShape.SizeHorCursor,
            "inside": Qt.CursorShape.OpenHandCursor,
        }.get(part, Qt.CursorShape.PointingHandCursor)
        self.setCursor(cursor)

    def finish_cycle_drag(self, x):
        original = self.cycle_drag.original
        mode = self.cycle_drag.mode
        if not self.cycle_drag.release():
            self.cycle_changed.emit(self.cycle)
        elif mode != "new" and original is not None:
            # A click on the region turns cycling on or off, as in Logic.
            toggled = CycleRegion(original.start, original.end, not original.enabled)
            self.cycle_changed.emit(toggled)
        else:
            # A click elsewhere in the ruler moves the playhead.
            self.cycle = original
            self.section_clicked.emit(x / max(self.width(), 1) * self.duration)

    def leaveEvent(self, event):
        """Drop the hover highlight when the pointer leaves."""
        if self.hover_section != -1:
            self.hover_section = -1
            self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if self.cycle_drag.active:
            self.finish_cycle_drag(event.position().x())
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

            section = self.sections[section_idx]
            loop_action = QAction("Loop This Section", self)
            loop_action.triggered.connect(
                lambda: self.cycle_changed.emit(
                    CycleRegion(float(section["start"]), float(section["end"]))
                )
            )
            menu.addAction(loop_action)

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
