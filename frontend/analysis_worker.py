#!/usr/bin/env python3
"""
Analysis Worker Module for Sectionist GUI

This module contains the AnalysisWorker class that handles
background audio analysis communication with the backend.
"""

import os

import requests
from PyQt6.QtCore import QThread, pyqtSignal

DEFAULT_BACKEND_URL = "http://127.0.0.1:5000"

# Analysis is synchronous on the backend: a 10 minute song can take a couple of
# minutes to process. This needs generous headroom so long files do not fail
# with "Analysis request timed out" while the backend is still working.
ANALYSIS_TIMEOUT_SECONDS = 600
HEALTH_TIMEOUT_SECONDS = 5


class AnalysisWorker(QThread):
    """Worker thread for analyzing audio files with the backend."""

    finished = pyqtSignal(dict)  # Analysis results
    error = pyqtSignal(str)  # Error message
    progress = pyqtSignal(str)  # Progress updates

    def __init__(self, file_path: str, backend_url: str = None):
        super().__init__()
        self.file_path = file_path
        self.backend_url = (
            backend_url or os.environ.get("SECTIONIST_BACKEND_URL", DEFAULT_BACKEND_URL)
        ).rstrip("/")

    def run(self):
        """Run the analysis in a background thread."""
        try:
            self.progress.emit("Checking backend connection...")

            # Check if backend is running
            health_response = requests.get(
                f"{self.backend_url}/health", timeout=HEALTH_TIMEOUT_SECONDS
            )
            if health_response.status_code != 200:
                self.error.emit("Backend server is not responding")
                return

            self.progress.emit("Uploading file for analysis...")

            # Analyze the audio file
            with open(self.file_path, "rb") as f:
                files = {"audio": f}
                response = requests.post(
                    f"{self.backend_url}/analyze",
                    files=files,
                    timeout=ANALYSIS_TIMEOUT_SECONDS,
                )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.progress.emit("Analysis completed successfully!")
                    self.finished.emit(result)
                else:
                    self.error.emit(
                        f"Analysis failed: {result.get('error', 'Unknown error')}"
                    )
            else:
                self.error.emit(f"Server error: {response.status_code}")

        except requests.exceptions.Timeout:
            self.error.emit("Analysis request timed out")
        except requests.exceptions.ConnectionError:
            self.error.emit(
                "Cannot connect to backend server. Make sure it's running on port 5000."
            )
        except Exception as e:
            self.error.emit(f"Analysis error: {str(e)}")
