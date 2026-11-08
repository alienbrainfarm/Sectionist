"""Integration tests for the frontend <-> backend request path.

The HTTP layer is exercised against stubs so the suite runs without a live
server. A real round-trip test is included but skipped unless the backend is
listening on port 8765.
"""

import os

import pytest
import requests

from analysis_worker import (
    ANALYSIS_TIMEOUT_SECONDS,
    HEALTH_TIMEOUT_SECONDS,
    AnalysisWorker,
)

BACKEND_URL = os.environ.get("SECTIONIST_BACKEND_URL", "http://127.0.0.1:8765")


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


def collect_signals(worker):
    """Capture everything the worker emits."""
    events = {"finished": [], "error": [], "progress": []}
    worker.finished.connect(events["finished"].append)
    worker.error.connect(events["error"].append)
    worker.progress.connect(events["progress"].append)
    return events


def test_analysis_timeout_leaves_room_for_long_songs():
    # A 10 minute song can take a couple of minutes to analyse; the old 60s
    # limit made long files fail while the backend was still working.
    assert ANALYSIS_TIMEOUT_SECONDS >= 300
    assert HEALTH_TIMEOUT_SECONDS <= 10


def test_run_uploads_file_and_emits_results(tmp_path, monkeypatch):
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"stand-in audio bytes")

    expected = {"success": True, "analysis": {"duration": 12.0}}
    calls = {}

    def fake_get(url, timeout=None):
        calls["get"] = {"url": url, "timeout": timeout}
        return FakeResponse(200, {"status": "healthy"})

    def fake_post(url, files=None, timeout=None):
        calls["post"] = {"url": url, "timeout": timeout, "files": files}
        return FakeResponse(200, expected)

    monkeypatch.setattr("analysis_worker.requests.get", fake_get)
    monkeypatch.setattr("analysis_worker.requests.post", fake_post)

    worker = AnalysisWorker(str(audio))
    events = collect_signals(worker)
    worker.run()

    assert events["error"] == []
    assert events["finished"] == [expected]
    assert calls["post"]["url"] == f"{BACKEND_URL}/analyze"
    assert calls["post"]["timeout"] == ANALYSIS_TIMEOUT_SECONDS
    assert calls["post"]["files"]["audio"].name.endswith("song.wav")


def test_run_reports_unreachable_backend(tmp_path, monkeypatch):
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"stand-in audio bytes")

    def unreachable(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr("analysis_worker.requests.get", unreachable)

    worker = AnalysisWorker(str(audio))
    events = collect_signals(worker)
    worker.run()

    assert events["finished"] == []
    assert len(events["error"]) == 1
    assert "Cannot connect" in events["error"][0]


def test_run_reports_analysis_error_payload(tmp_path, monkeypatch):
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"stand-in audio bytes")

    monkeypatch.setattr(
        "analysis_worker.requests.get", lambda *a, **k: FakeResponse(200, {})
    )
    monkeypatch.setattr(
        "analysis_worker.requests.post",
        lambda *a, **k: FakeResponse(200, {"success": False, "error": "bad file"}),
    )

    worker = AnalysisWorker(str(audio))
    events = collect_signals(worker)
    worker.run()

    assert events["finished"] == []
    assert len(events["error"]) == 1
    assert "bad file" in events["error"][0]


def test_run_reports_server_error_status(tmp_path, monkeypatch):
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"stand-in audio bytes")

    monkeypatch.setattr(
        "analysis_worker.requests.get", lambda *a, **k: FakeResponse(200, {})
    )
    monkeypatch.setattr(
        "analysis_worker.requests.post", lambda *a, **k: FakeResponse(500)
    )

    worker = AnalysisWorker(str(audio))
    events = collect_signals(worker)
    worker.run()

    assert len(events["error"]) == 1
    assert "500" in events["error"][0]


def backend_is_running():
    try:
        requests.get(f"{BACKEND_URL}/health", timeout=1).raise_for_status()
    except requests.exceptions.RequestException:
        return False
    return True


@pytest.mark.skipif(
    not backend_is_running(), reason=f"no backend listening on {BACKEND_URL}"
)
def test_live_backend_reports_health_and_formats():
    health = requests.get(f"{BACKEND_URL}/health", timeout=5)
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    formats = requests.get(f"{BACKEND_URL}/formats", timeout=5)
    assert formats.status_code == 200
    assert "mp3" in formats.json()["supported_formats"]
