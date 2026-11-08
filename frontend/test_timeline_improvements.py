"""Unit tests for timeline widget behaviour."""

import pytest
from unittest.mock import MagicMock

from timeline_widget import TimelineWidget

SECTIONS = [
    {"start": 0, "end": 30, "name": "intro"},
    {"start": 30, "end": 60, "name": "verse"},
    {"start": 60, "end": 90, "name": "chorus"},
]


@pytest.fixture
def timeline(qapp):
    widget = TimelineWidget()
    widget.resize(800, 120)
    widget.set_sections(SECTIONS)
    widget.set_duration(180)
    yield widget
    widget.close()


def test_sections_and_duration_recorded(timeline):
    assert len(timeline.sections) == 3
    assert timeline.duration == 180


def test_drag_time_display_is_stored(timeline):
    timeline.drag_time_display = "1:15.500"
    assert timeline.drag_time_display == "1:15.500"


def test_section_position_detection(timeline):
    # x is mapped to time as x/width * duration (800px == 180s).
    assert timeline.get_section_at_position(50) == 0
    assert timeline.get_section_at_position(200) == 1
    assert timeline.get_section_at_position(350) == 2


def test_position_outside_any_section_returns_minus_one(timeline):
    # 700px -> 157.5s, past the last section (ends at 90s).
    assert timeline.get_section_at_position(700) == -1


def test_split_and_join_signals_exist(timeline):
    assert hasattr(timeline, "section_split")
    assert hasattr(timeline, "section_joined")
    assert hasattr(timeline, "section_renamed")
    assert hasattr(timeline, "section_resized")


def test_split_section_emits_midpoint(timeline):
    handler = MagicMock()
    timeline.section_split.connect(handler)

    timeline.split_section_at_position(1, 400)

    handler.assert_called_once()
    section_index, split_time = handler.call_args[0]
    assert section_index == 1
    assert split_time == 45.0  # midpoint of the 30-60s verse


def test_split_out_of_range_section_is_ignored(timeline):
    handler = MagicMock()
    timeline.section_split.connect(handler)

    timeline.split_section_at_position(99, 400)

    handler.assert_not_called()
