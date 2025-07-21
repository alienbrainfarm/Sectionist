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
    y1 = (
        0.5 * np.sin(2 * np.pi * 261.63 * t[: sr * 10])  # C4
        + 0.3 * np.sin(2 * np.pi * 329.63 * t[: sr * 10])  # E4
        + 0.3 * np.sin(2 * np.pi * 392.00 * t[: sr * 10])
    )  # G4

    # Second part: G major chord (G-B-D)
    y2 = (
        0.5 * np.sin(2 * np.pi * 392.00 * t[: sr * 10])  # G4
        + 0.3 * np.sin(2 * np.pi * 493.88 * t[: sr * 10])  # B4
        + 0.3 * np.sin(2 * np.pi * 587.33 * t[: sr * 10])
    )  # D5

    # Third part: Back to C major
    y3 = (
        0.5 * np.sin(2 * np.pi * 261.63 * t[: sr * 10])  # C4
        + 0.3 * np.sin(2 * np.pi * 329.63 * t[: sr * 10])  # E4
        + 0.3 * np.sin(2 * np.pi * 392.00 * t[: sr * 10])
    )  # G4

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
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    for note in note_names:
        expected_keys.extend([f"{note} major", f"{note} minor"])

    assert detected_key in expected_keys


def test_chord_detection_basic():
    """Test basic chord detection functionality."""
    from example import detect_chords

    # Create test audio with a C major chord (C-E-G)
    sr = 22050
    duration = 5  # 5 seconds
    t = np.linspace(0, duration, duration * sr)

    # C major chord frequencies: C4=261.63, E4=329.63, G4=392.00
    y = (
        0.5 * np.sin(2 * np.pi * 261.63 * t)
        + 0.3 * np.sin(2 * np.pi * 329.63 * t)
        + 0.3 * np.sin(2 * np.pi * 392.00 * t)
    )

    chords = detect_chords(y, sr)

    # Should detect some chords
    assert isinstance(chords, list)

    # Each chord should have proper structure
    for chord in chords:
        assert isinstance(chord, dict)
        assert "name" in chord
        assert "start" in chord
        assert "end" in chord
        assert "confidence" in chord
        assert isinstance(chord["name"], str)
        assert isinstance(chord["start"], (int, float))
        assert isinstance(chord["end"], (int, float))
        assert isinstance(chord["confidence"], (int, float))
        assert 0 <= chord["confidence"] <= 1
        assert chord["start"] < chord["end"]


def test_chord_detection_multiple_chords():
    """Test chord detection with multiple different chords."""
    from example import detect_chords

    sr = 22050
    segment_duration = 2  # 2 seconds per chord

    # Create a progression: C major -> F major -> G major
    t1 = np.linspace(0, segment_duration, segment_duration * sr)
    t2 = np.linspace(segment_duration, segment_duration * 2, segment_duration * sr)
    t3 = np.linspace(segment_duration * 2, segment_duration * 3, segment_duration * sr)

    # C major (C-E-G): 261.63, 329.63, 392.00
    c_major = (
        0.5 * np.sin(2 * np.pi * 261.63 * t1)
        + 0.3 * np.sin(2 * np.pi * 329.63 * t1)
        + 0.3 * np.sin(2 * np.pi * 392.00 * t1)
    )

    # F major (F-A-C): 349.23, 440.00, 523.25
    f_major = (
        0.5 * np.sin(2 * np.pi * 349.23 * t2)
        + 0.3 * np.sin(2 * np.pi * 440.00 * t2)
        + 0.3 * np.sin(2 * np.pi * 523.25 * t2)
    )

    # G major (G-B-D): 392.00, 493.88, 587.33
    g_major = (
        0.5 * np.sin(2 * np.pi * 392.00 * t3)
        + 0.3 * np.sin(2 * np.pi * 493.88 * t3)
        + 0.3 * np.sin(2 * np.pi * 587.33 * t3)
    )

    # Combine all segments
    y = np.concatenate([c_major, f_major, g_major])

    chords = detect_chords(y, sr)

    # Should detect chords
    assert len(chords) >= 1
    assert isinstance(chords, list)

    # Verify chord progression covers expected time range
    if chords:
        first_start = min(chord["start"] for chord in chords)
        last_end = max(chord["end"] for chord in chords)
        assert first_start < 2.0  # Should start early
        assert last_end > 4.0  # Should cover most of the audio


def test_chord_detection_integration():
    """Test that chord detection integrates properly with analyze_audio_file."""
    from example import analyze_audio_file
    import tempfile
    import soundfile as sf

    # Create test audio data
    sr = 22050
    duration = 10
    t = np.linspace(0, duration, duration * sr)

    # Simple C major chord
    y = (
        0.5 * np.sin(2 * np.pi * 261.63 * t)
        + 0.3 * np.sin(2 * np.pi * 329.63 * t)
        + 0.3 * np.sin(2 * np.pi * 392.00 * t)
    )

    # Save as temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, y, sr)
        temp_path = tmp.name

    try:
        # Analyze the file
        results = analyze_audio_file(temp_path)

        # Verify the results include chord information
        assert "chords" in results
        assert isinstance(results["chords"], list)

        # If chords are detected, verify structure
        for chord in results["chords"]:
            assert isinstance(chord, dict)
            assert "name" in chord
            assert "start" in chord
            assert "end" in chord
            assert "confidence" in chord

    finally:
        # Clean up
        import os

        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_empty_audio_chord_detection():
    """Test chord detection with silent/empty audio."""
    from example import detect_chords

    # Create silent audio
    sr = 22050
    duration = 5
    y = np.zeros(duration * sr)

    chords = detect_chords(y, sr)

    # Should return empty list or very few low-confidence chords
    assert isinstance(chords, list)
    # Silent audio should not detect high-confidence chords
    for chord in chords:
        assert chord["confidence"] < 0.8  # Low confidence expected for silence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
