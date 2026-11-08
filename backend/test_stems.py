"""Tests for stem separation: caching, progress, jobs and the /stems endpoints.

Demucs itself is replaced by a fake that returns tones, so these run without
the model or torch installed.
"""

import io

import numpy as np
import pytest
import soundfile as sf


class FakeTensor:
    def __init__(self, samples):
        self.samples = samples

    def cpu(self):
        return self

    def numpy(self):
        return self.samples


class FakeSeparator:
    samplerate = 8000

    def __init__(self):
        self.calls = 0
        self.callback = None

    def update_parameter(self, callback=None):
        self.callback = callback

    def separate_audio_file(self, path):
        self.calls += 1
        length = 4000
        if self.callback:
            self.callback({"audio_length": length, "segment_offset": 2000})
        tone = 0.5 * np.sin(np.linspace(0, 200, length))
        stems = {
            name: FakeTensor(np.stack([tone * gain, tone * gain]))
            for name, gain in (("other", 0.2), ("vocals", 1.0), ("drums", 0.5))
        }
        return None, stems


@pytest.fixture
def fake_demucs(monkeypatch, tmp_path):
    from analysis import stems

    separator = FakeSeparator()
    monkeypatch.setenv(stems.CACHE_ENV, str(tmp_path / "cache"))
    monkeypatch.setattr(stems, "_separator", lambda model: separator)
    monkeypatch.setattr(stems, "stems_available", lambda: True)
    return separator


@pytest.fixture
def song(tmp_path):
    path = tmp_path / "song.wav"
    sf.write(path, np.zeros((800, 2)), 8000)
    return path


def test_separate_writes_flac_stems_in_display_order(fake_demucs, song):
    from analysis import stems

    seen = []
    result = stems.separate(song, progress=seen.append)

    assert list(result) == ["vocals", "drums", "other"]
    data, rate = sf.read(result["vocals"])
    assert rate == 8000 and data.shape == (4000, 2)
    assert seen == [0.5]


def test_separation_is_cached_by_content_not_path(fake_demucs, song, tmp_path):
    from analysis import stems

    stems.separate(song)
    copy = tmp_path / "upload-1234.wav"
    copy.write_bytes(song.read_bytes())

    stems.separate(copy)
    assert fake_demucs.calls == 1


def test_incomplete_cache_is_ignored(fake_demucs, song):
    from analysis import stems

    result = stems.separate(song)
    result["drums"].unlink()

    stems.separate(song)
    assert fake_demucs.calls == 2


def test_unknown_model_is_rejected(fake_demucs, song):
    from analysis import stems

    with pytest.raises(ValueError):
        stems.separate(song, model="nope")


def test_progress_covers_every_model_in_a_bag():
    from analysis.stems import progress_fraction

    assert progress_fraction({}) == 0.0
    first = {"audio_length": 100, "segment_offset": 50, "models": 4}
    assert progress_fraction(first) == pytest.approx(0.125)
    last = dict(first, model_idx_in_bag=3, segment_offset=100)
    assert progress_fraction(last) == 1.0


def test_vocals_for_lyrics_reuse_the_stem_cache(fake_demucs, song, monkeypatch):
    from analysis import stems

    monkeypatch.setenv(stems.STEMS_ENV, "1")
    vocals = stems.vocals_path(song)
    assert vocals.name == "vocals.flac"
    stems.separate(song)
    assert fake_demucs.calls == 1


def test_failed_job_reports_the_error_and_removes_the_upload(tmp_path):
    from analysis import stem_jobs

    upload = tmp_path / "upload.wav"
    upload.write_bytes(b"x")

    def broken(path, model, progress):
        raise RuntimeError("model download failed")

    job = stem_jobs.start_job(upload, "htdemucs", separate=broken, background=False)
    assert job.info()["status"] == "error"
    assert job.info()["error"] == "model download failed"
    assert not upload.exists()


# --- endpoints ---------------------------------------------------------------


@pytest.fixture
def client(fake_demucs, monkeypatch):
    import server
    from analysis import stem_jobs

    monkeypatch.setattr(
        server,
        "start_stem_job",
        lambda path, model: stem_jobs.start_job(path, model, background=False),
    )
    server.app.config["TESTING"] = True
    with server.app.test_client() as client:
        yield client


def upload(client, song, **form):
    data = {"audio": (io.BytesIO(song.read_bytes()), "My Song.wav"), **form}
    return client.post("/stems", data=data, content_type="multipart/form-data")


def test_stem_job_round_trip(client, song):
    started = upload(client, song)
    assert started.status_code == 202
    job_id = started.get_json()["job_id"]

    status = client.get(f"/stems/{job_id}").get_json()
    assert status["status"] == "done"
    assert status["stems"] == ["vocals", "drums", "other"]

    stem = client.get(f"/stems/{job_id}/vocals")
    assert stem.status_code == 200
    assert stem.mimetype == "audio/flac"
    data, _rate = sf.read(io.BytesIO(stem.data))
    assert data.shape == (4000, 2)

    assert client.get(f"/stems/{job_id}/bass").status_code == 404
    assert client.get("/stems/missing").status_code == 404


def test_stems_reject_unknown_models_and_missing_files(client, song):
    assert upload(client, song, model="spleeter").status_code == 400
    response = client.post("/stems", data={}, content_type="multipart/form-data")
    assert response.status_code == 400


def test_stems_explain_how_to_install_demucs(client, song, monkeypatch):
    from analysis import stems

    monkeypatch.setattr(stems, "stems_available", lambda: False)
    response = upload(client, song)
    assert response.status_code == 503
    assert "requirements-stems.txt" in response.get_json()["error"]


def test_health_lists_stem_models(client):
    info = client.get("/health").get_json()["stems"]
    assert info["available"] is True
    assert info["default"] == "htdemucs"
    assert "htdemucs_6s" in info["models"]
