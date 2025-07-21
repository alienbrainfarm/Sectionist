#!/usr/bin/env python3
"""
Unit tests for the Flask server API.
"""

import pytest
import tempfile
import os
from unittest.mock import patch
import soundfile as sf
import numpy as np


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    from server import app

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.get_json()
    assert "status" in data
    assert "version" in data
    assert "backend" in data
    assert data["status"] == "healthy"


def test_supported_formats_endpoint(client):
    """Test the supported formats endpoint."""
    response = client.get("/formats")
    assert response.status_code == 200

    data = response.get_json()
    assert "supported_formats" in data
    assert isinstance(data["supported_formats"], list)
    assert len(data["supported_formats"]) > 0
    assert "mp3" in data["supported_formats"]
    assert "wav" in data["supported_formats"]


def test_analyze_no_file(client):
    """Test analyze endpoint with no file provided."""
    response = client.post("/analyze")
    assert response.status_code == 400

    data = response.get_json()
    assert "error" in data
    assert data["error"] == "No audio file provided"


def test_analyze_empty_filename(client):
    """Test analyze endpoint with empty filename."""
    data = {"audio": (None, "")}
    response = client.post("/analyze", data=data)
    assert response.status_code == 400

    data = response.get_json()
    assert "error" in data
    assert data["error"] == "No file selected"


def test_analyze_unsupported_format(client):
    """Test analyze endpoint with unsupported file format."""
    data = {"audio": (tempfile.NamedTemporaryFile(suffix=".txt"), "test.txt")}
    response = client.post("/analyze", data=data, content_type="multipart/form-data")
    assert response.status_code == 400

    response_data = response.get_json()
    assert "error" in response_data
    assert "Unsupported file format" in response_data["error"]


@patch("server.analyze_audio_file")
def test_analyze_success(mock_analyze, client):
    """Test successful audio analysis."""
    # Mock the analysis function to return expected data
    mock_analyze.return_value = {
        "duration": 30.0,
        "tempo": 120.0,
        "key": "C major",
        "key_changes": [{"timestamp": 15.0, "from_key": "C major", "to_key": "G major", "confidence": 0.8}],
        "sections": [{"name": "Intro", "start": 0.0, "end": 5.0, "confidence": 0.9}],
        "beats_detected": 60,
        "chords": [
            {"name": "C", "start": 0.0, "end": 4.0, "confidence": 0.85},
            {"name": "F", "start": 4.0, "end": 8.0, "confidence": 0.82}
        ],
    }

    # Create a temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        # Create simple audio data
        sr = 22050
        duration = 1.0  # 1 second
        t = np.linspace(0, duration, int(duration * sr))
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440Hz tone

        # Write audio file
        sf.write(tmp, audio_data, sr)
        tmp.flush()

        try:
            # Test the endpoint
            with open(tmp.name, "rb") as audio_file:
                data = {"audio": (audio_file, "test.wav")}
                response = client.post(
                    "/analyze", data=data, content_type="multipart/form-data"
                )

            assert response.status_code == 200

            response_data = response.get_json()
            assert response_data["success"] is True
            assert "file_name" in response_data
            assert "analysis" in response_data

            analysis = response_data["analysis"]
            assert analysis["duration"] == 30.0
            assert analysis["tempo"] == 120.0
            assert analysis["key"] == "C major"
            assert "key_changes" in analysis
            assert isinstance(analysis["key_changes"], list)
            assert len(analysis["sections"]) == 1
            assert analysis["beats_detected"] == 60
            
            # Test chord information
            assert "chords" in analysis
            assert isinstance(analysis["chords"], list)
            assert len(analysis["chords"]) == 2
            
            # Verify chord structure
            chord = analysis["chords"][0]
            assert chord["name"] == "C"
            assert chord["start"] == 0.0
            assert chord["end"] == 4.0
            assert chord["confidence"] == 0.85

        finally:
            # Clean up
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)


@patch("server.analyze_audio_file")
def test_analyze_error(mock_analyze, client):
    """Test analyze endpoint when analysis fails."""
    # Mock the analysis function to raise an exception
    mock_analyze.side_effect = Exception("Analysis failed")

    # Create a temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        # Create simple audio data
        sr = 22050
        duration = 1.0
        t = np.linspace(0, duration, int(duration * sr))
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

        # Write audio file
        sf.write(tmp, audio_data, sr)
        tmp.flush()

        try:
            # Test the endpoint
            with open(tmp.name, "rb") as audio_file:
                data = {"audio": (audio_file, "test.wav")}
                response = client.post(
                    "/analyze", data=data, content_type="multipart/form-data"
                )

            assert response.status_code == 500

            response_data = response.get_json()
            assert response_data["success"] is False
            assert "error" in response_data
            assert "Analysis failed" in response_data["error"]

        finally:
            # Clean up
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)


def test_allowed_file():
    """Test the allowed_file function."""
    from server import allowed_file

    # Test allowed extensions
    assert allowed_file("test.mp3") is True
    assert allowed_file("test.wav") is True
    assert allowed_file("test.aiff") is True
    assert allowed_file("test.m4a") is True
    assert allowed_file("test.flac") is True

    # Test disallowed extensions
    assert allowed_file("test.txt") is False
    assert allowed_file("test.pdf") is False
    assert allowed_file("test") is False
    assert allowed_file("") is False

    # Test case insensitivity
    assert allowed_file("test.MP3") is True
    assert allowed_file("test.WAV") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
