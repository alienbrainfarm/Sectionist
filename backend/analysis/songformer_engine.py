"""Supervised segmentation with SongFormer.

SongFormer predicts section boundaries and functional labels (intro, verse,
pre-chorus, chorus, bridge, instrumental, silence, outro) directly from the
audio. It replaces the heuristic segmentation from ``example.py`` while the
tempo, key, beat and chord estimates still come from the librosa pipeline.

Optional: this module imports torch and transformers lazily, so the backend
runs without them. See docs/MODEL_RESEARCH.md for setup and measured timings.
"""

import importlib.util
import os
import sys
import threading
from pathlib import Path

from .base import Analyzer
from .librosa_engine import LibrosaAnalyzer
from .sections import to_sections

SAMPLE_RATE = 24000
MODEL_DIR_ENV = "SECTIONIST_MODEL_DIR"
DEVICE_ENV = "SECTIONIST_DEVICE"

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_DIR = REPO_ROOT / ".hf-cache" / "SongFormer"

_models = {}
_model_lock = threading.Lock()
_inference_lock = threading.Lock()


def model_dir():
    """Directory holding the SongFormer checkpoint."""
    configured = os.environ.get(MODEL_DIR_ENV)
    return Path(configured).expanduser() if configured else DEFAULT_MODEL_DIR


def songformer_available():
    """True when this engine could actually run."""
    if importlib.util.find_spec("torch") is None:
        return False
    if importlib.util.find_spec("transformers") is None:
        return False
    directory = model_dir()
    return directory.is_dir() and (directory / "config.json").exists()


def resolve_device(requested=None):
    """Pick an inference device.

    CUDA is used automatically when present. Apple's MPS is deliberately *not*
    selected automatically: it is faster on short inputs but collapses on
    longer ones on unified-memory machines (measured in docs/MODEL_RESEARCH.md).
    Set ``SECTIONIST_DEVICE=mps`` to opt in.
    """
    choice = (requested or os.environ.get(DEVICE_ENV, "auto") or "auto").strip().lower()
    if choice not in ("", "auto"):
        return choice

    import torch

    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _load_model(directory, device):
    key = (str(directory), device)
    with _model_lock:
        if key in _models:
            return _models[key]

        from transformers import AutoModel

        # The checkpoint's remote code imports its vendored modules by bare
        # name, so its directory has to be importable.
        if str(directory) not in sys.path:
            sys.path.insert(0, str(directory))
        os.environ.setdefault("SONGFORMER_LOCAL_DIR", str(directory))

        model = AutoModel.from_pretrained(
            str(directory), trust_remote_code=True, low_cpu_mem_usage=False
        )
        model.eval()
        model.to(device)
        _models[key] = model
        return model


class SongFormerAnalyzer(Analyzer):
    """Section detection from SongFormer, everything else from librosa."""

    name = "songformer"

    def __init__(self, directory=None, device=None):
        self.directory = Path(directory) if directory else model_dir()
        self._requested_device = device
        self._device = None
        self._baseline = LibrosaAnalyzer()

    @property
    def device(self):
        # Resolved lazily so constructing the engine never imports torch.
        if self._device is None:
            self._device = resolve_device(self._requested_device)
        return self._device

    def _model(self):
        return _load_model(self.directory, self.device)

    def analyze(self, file_path: str) -> dict:
        import librosa
        import torch

        # Tempo, key, beats and chords still come from the existing pipeline.
        result = self._baseline.analyze(file_path)

        audio, _ = librosa.load(file_path, sr=SAMPLE_RATE, mono=True)
        tensor = torch.from_numpy(audio).to(self.device)

        model = self._model()
        with _inference_lock, torch.inference_mode():
            predicted = model(tensor)

        result["sections"] = to_sections(predicted)
        result["engine"] = self.name
        return result
