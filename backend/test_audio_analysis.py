#!/usr/bin/env python3
"""
Unit tests for audio analysis functionality.
"""

import pytest
import numpy as np
import tempfile
import os
from unittest.mock import patch
from example import analyze_audio_file


def test_analyze_audio_file_nonexistent():
    """Test that analyzing a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        analyze_audio_file("/path/that/does/not/exist.mp3")


def test_analyze_song_structure_basic():
    """Test basic song structure analysis with synthetic data."""
    from example import analyze_song_structure

    # Create simple synthetic audio data
    sr = 22050
    duration = 10  # 10 seconds
    t = np.linspace(0, duration, duration * sr)
    y = 0.5 * np.sin(2 * np.pi * 440 * t)  # Simple 440Hz tone

    sections = analyze_song_structure(y, sr)

    assert isinstance(sections, list)
    assert len(sections) > 0
    assert all("name" in section for section in sections)
    assert all("start" in section for section in sections)
    assert all("end" in section for section in sections)
    assert all("confidence" in section for section in sections)


@patch("example.librosa.load")
@patch("example.librosa.beat.beat_track")
@patch("example.librosa.feature.chroma_stft")
def test_analyze_audio_file_mocked(mock_chroma, mock_beat, mock_load):
    """Test audio file analysis with mocked librosa functions."""
    # Mock librosa.load
    mock_audio = np.random.random(22050 * 30)  # 30 seconds of random audio
    mock_load.return_value = (mock_audio, 22050)

    # Mock beat tracking
    mock_beat.return_value = (120.0, np.arange(0, 30, 0.5))  # 120 BPM, beats every 0.5s

    # Mock chroma features
    mock_chroma.return_value = np.random.random((12, 100))  # 12 chroma bins, 100 frames

    # Create a temporary file path (doesn't need to exist due to mocking)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        temp_path = tmp.name

    try:
        # Mock os.path.exists to return True
        with patch("os.path.exists", return_value=True):
            result = analyze_audio_file(temp_path)

        # Verify result structure
        assert isinstance(result, dict)
        assert "file_path" in result
        assert "duration" in result
        assert "tempo" in result
        assert "key" in result
        assert "key_changes" in result
        assert "sections" in result
        assert "beats_detected" in result

        assert result["file_path"] == temp_path
        assert isinstance(result["duration"], (int, float))
        assert isinstance(result["tempo"], (int, float))
        assert isinstance(result["key"], str)
        assert isinstance(result["key_changes"], list)
        assert isinstance(result["sections"], list)
        assert isinstance(result["beats_detected"], int)

    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_song_section_structure():
    """Test that song sections have the expected structure."""
    from example import analyze_song_structure

    # Create test audio data
    sr = 22050
    duration = 5  # 5 seconds
    t = np.linspace(0, duration, duration * sr)
    # Create audio with some variation
    y = (
        0.5 * np.sin(2 * np.pi * 440 * t)
        + 0.3 * np.sin(2 * np.pi * 880 * t)
        + 0.1 * np.random.random(len(t))
    )

    sections = analyze_song_structure(y, sr)

    # Verify each section has required fields
    for section in sections:
        assert isinstance(section, dict)
        assert "name" in section
        assert "start" in section
        assert "end" in section
        assert "confidence" in section

        # Verify field types and ranges
        assert isinstance(section["name"], str)
        assert isinstance(section["start"], (int, float))
        assert isinstance(section["end"], (int, float))
        assert isinstance(section["confidence"], (int, float))

        # Verify logical constraints
        assert section["start"] >= 0
        assert section["end"] > section["start"]
        assert 0 <= section["confidence"] <= 1


def test_key_detection_and_changes():
    """Test enhanced key detection and key change detection."""
    from example import detect_key_and_changes
    
    # Create test audio data with different harmonic content
    sr = 22050
    duration = 30  # 30 seconds to test key changes
    t = np.linspace(0, duration, duration * sr)
    
    # First part: C major chord (C-E-G)
    y1 = (0.5 * np.sin(2 * np.pi * 261.63 * t[:sr*10]) +  # C4
          0.3 * np.sin(2 * np.pi * 329.63 * t[:sr*10]) +  # E4
          0.3 * np.sin(2 * np.pi * 392.00 * t[:sr*10]))   # G4
    
    # Second part: G major chord (G-B-D) 
    y2 = (0.5 * np.sin(2 * np.pi * 392.00 * t[:sr*10]) +  # G4
          0.3 * np.sin(2 * np.pi * 493.88 * t[:sr*10]) +  # B4
          0.3 * np.sin(2 * np.pi * 587.33 * t[:sr*10]))   # D5
          
    # Third part: Back to C major
    y3 = (0.5 * np.sin(2 * np.pi * 261.63 * t[:sr*10]) +  # C4
          0.3 * np.sin(2 * np.pi * 329.63 * t[:sr*10]) +  # E4
          0.3 * np.sin(2 * np.pi * 392.00 * t[:sr*10]))   # G4
    
    # Combine all parts
    y = np.concatenate([y1, y2, y3])
    
    # Test key detection
    detected_key, key_changes = detect_key_and_changes(y, sr)
    
    # Verify key detection returns valid results
    assert isinstance(detected_key, str)
    assert "major" in detected_key or "minor" in detected_key
    assert isinstance(key_changes, list)
    
    # Each key change should have proper structure
    for change in key_changes:
        assert isinstance(change, dict)
        assert "timestamp" in change
        assert "from_key" in change 
        assert "to_key" in change
        assert "confidence" in change
        assert isinstance(change["timestamp"], (int, float))
        assert isinstance(change["from_key"], str)
        assert isinstance(change["to_key"], str)
        assert isinstance(change["confidence"], (int, float))
        assert 0 <= change["confidence"] <= 1


def test_key_profiles_coverage():
    """Test that all 24 keys are properly defined."""
    from example import detect_key_and_changes
    
    # Create simple test audio
    sr = 22050
    t = np.linspace(0, 5, 5 * sr)
    y = 0.5 * np.sin(2 * np.pi * 440 * t)  # Simple A4 tone
    
    # Test that function executes without error
    detected_key, key_changes = detect_key_and_changes(y, sr)
    
    # Should detect one of the 24 possible keys
    expected_keys = []
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    for note in note_names:
        expected_keys.extend([f"{note} major", f"{note} minor"])
    
    assert detected_key in expected_keys


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
