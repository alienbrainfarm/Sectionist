"""Fetches stems from the backend and keeps a local copy of them.

The backend may be on another machine, so stems come back over HTTP as FLAC
and are kept in the user's data folder, keyed by the song's contents and the
model. Reopening a song finds them there without asking the backend again.
Decoding happens here too, off the UI thread: four stems of a four-minute song
take a second or two to decode.
"""

import hashlib
import json
import os
import shutil
import tempfile
import time
from pathlib import Path

import requests
from PyQt6.QtCore import QStandardPaths, QThread, pyqtSignal

try:
    from .analysis_worker import DEFAULT_BACKEND_URL
    from .stem_player import load_stem_set
except ImportError:
    from analysis_worker import DEFAULT_BACKEND_URL
    from stem_player import load_stem_set

# Keep in step with MODELS in backend/analysis/stems.py.
STEM_MODELS = (
    ("htdemucs", "4 stems"),
    ("htdemucs_ft", "4 stems, high quality (slower)"),
    ("htdemucs_6s", "6 stems: adds guitar and piano"),
)
DEFAULT_MODEL = STEM_MODELS[0][0]
MANIFEST = "stems.json"
POLL_SECONDS = 0.5
REQUEST_TIMEOUT = 30
JOB_TIMEOUT = 30 * 60  # a long song with the slow model on a CPU


def cache_root():
    override = os.environ.get("SECTIONIST_STEMS_DIR")
    if override:
        return Path(override)
    base = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    )
    return Path(base or Path.home() / ".sectionist") / "stems"


def content_key(file_path):
    digest = hashlib.sha1()
    with open(file_path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()[:16]


def cached_stems(key, model):
    """{name: path} for stems already downloaded for this song and model."""
    folder = cache_root() / f"{key}-{model}"
    try:
        names = json.loads((folder / MANIFEST).read_text(encoding="utf-8"))["stems"]
    except (OSError, ValueError, KeyError):
        return None
    paths = {name: folder / f"{name}.flac" for name in names}
    return paths if all(p.exists() for p in paths.values()) else None


def find_cached(key):
    """The first model with stems on disk for this song: (model, paths)."""
    for model, _label in STEM_MODELS:
        paths = cached_stems(key, model)
        if paths:
            return model, paths
    return None, None


class StemsWorker(QThread):
    """Gets stems for a song, from the local cache or the backend.

    With ``model=None`` it only looks in the cache, which is what happens when
    a song is opened: stems appear if they were split before, and nothing is
    sent to the backend otherwise.
    """

    progress = pyqtSignal(float, str)  # fraction (or -1 when unknown), message
    finished = pyqtSignal(object)  # StemSet, or None when nothing was cached
    error = pyqtSignal(str)

    def __init__(self, file_path, model=None, backend_url=None):
        super().__init__()
        self.file_path = file_path
        self.model = model
        self.backend_url = (
            backend_url or os.environ.get("SECTIONIST_BACKEND_URL", DEFAULT_BACKEND_URL)
        ).rstrip("/")

    def run(self):
        try:
            self.finished.emit(self.fetch())
        except requests.exceptions.ConnectionError:
            self.error.emit("Cannot connect to the backend to split stems.")
        except Exception as error:
            self.error.emit(str(error) or error.__class__.__name__)

    def fetch(self):
        key = content_key(self.file_path)
        if self.model is None:
            model, paths = find_cached(key)
            if not paths:
                return None
        else:
            model = self.model
            paths = cached_stems(key, model) or self.download(key, model)
        if paths is None:
            return None
        self.progress.emit(-1, "Loading stems…")
        return load_stem_set(paths, model)

    def download(self, key, model):
        self.progress.emit(-1, "Uploading song for stem splitting…")
        with open(self.file_path, "rb") as handle:
            response = requests.post(
                f"{self.backend_url}/stems",
                files={"audio": (Path(self.file_path).name, handle)},
                data={"model": model},
                timeout=REQUEST_TIMEOUT * 4,
            )
        job = self._json(response)
        job_id = job["job_id"]

        deadline = time.monotonic() + JOB_TIMEOUT
        while job["status"] not in ("done", "error"):
            if self.isInterruptionRequested():
                return None
            if time.monotonic() > deadline:
                raise RuntimeError("Stem splitting took too long.")
            fraction = float(job.get("progress") or 0)
            self.progress.emit(fraction, f"Splitting stems… {fraction:.0%}")
            time.sleep(POLL_SECONDS)
            job = self._json(
                requests.get(
                    f"{self.backend_url}/stems/{job_id}", timeout=REQUEST_TIMEOUT
                )
            )
        if job["status"] == "error":
            raise RuntimeError(f"Stem splitting failed: {job.get('error')}")

        root = cache_root()
        root.mkdir(parents=True, exist_ok=True)
        scratch = Path(tempfile.mkdtemp(dir=root))
        try:
            for index, name in enumerate(job["stems"]):
                self.progress.emit(
                    index / len(job["stems"]), f"Downloading {name} stem…"
                )
                url = f"{self.backend_url}/stems/{job_id}/{name}"
                with requests.get(url, stream=True, timeout=REQUEST_TIMEOUT) as reply:
                    reply.raise_for_status()
                    with open(scratch / f"{name}.flac", "wb") as out:
                        for chunk in reply.iter_content(1 << 16):
                            out.write(chunk)
            manifest = {"stems": job["stems"], "model": model}
            (scratch / MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
            folder = root / f"{key}-{model}"
            shutil.rmtree(folder, ignore_errors=True)
            scratch.rename(folder)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        return cached_stems(key, model)

    @staticmethod
    def _json(response):
        try:
            body = response.json()
        except ValueError:
            body = {}
        if response.status_code >= 400:
            raise RuntimeError(
                body.get("error") or f"Server error {response.status_code}"
            )
        return body
