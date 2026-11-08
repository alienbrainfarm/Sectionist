"""Supervised segmentation with SongFormer.

SongFormer predicts section boundaries and functional labels (intro, verse,
pre-chorus, chorus, bridge, instrumental, silence, outro) directly from the
audio. It replaces the heuristic segmentation from ``example.py`` while the
tempo, key and chord estimates still come from the librosa pipeline.

Beat This! is used, when installed, for the beat count and to snap section
boundaries onto downbeats so sections line up with bars.

A label model trained on corrected songs (see ``tools/train_label_model.py``)
can be loaded to adjust the network's labels; it is optional and absent by
default.

Optional: torch and transformers are imported lazily, so the backend runs
without them. See docs/MODEL_RESEARCH.md for setup and measured timings.
"""

import importlib.util
import os
import sys
import threading
from pathlib import Path

import numpy as np

from .base import Analyzer
from .calibration import SoftmaxRegression, apply_calibration, reduce_probabilities
from .device import resolve_device
from .librosa_engine import LibrosaAnalyzer
from .sections import finalize_sections, prepare_segments, snap_boundaries

SAMPLE_RATE = 24000
MODEL_DIR_ENV = "SECTIONIST_MODEL_DIR"
LABEL_MODEL_ENV = "SECTIONIST_LABEL_MODEL"

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_DIR = REPO_ROOT / ".hf-cache" / "SongFormer"
DEFAULT_LABEL_MODEL = REPO_ROOT / ".hf-cache" / "label_model.npz"

_models = {}
_model_lock = threading.Lock()
_inference_lock = threading.Lock()

# Filled in by the post-processing hook installed on the loaded model.
_capture = {}

_label_model = None
_label_model_loaded = False


def model_dir():
    """Directory holding the SongFormer checkpoint."""
    configured = os.environ.get(MODEL_DIR_ENV)
    return Path(configured).expanduser() if configured else DEFAULT_MODEL_DIR


def label_model_path():
    configured = os.environ.get(LABEL_MODEL_ENV)
    return Path(configured).expanduser() if configured else DEFAULT_LABEL_MODEL


def load_label_model():
    """Load the optional correction model, or return None."""
    global _label_model, _label_model_loaded
    if not _label_model_loaded:
        path = label_model_path()
        _label_model = SoftmaxRegression.load(path) if path.exists() else None
        _label_model_loaded = True
    return _label_model


def songformer_available():
    """True when this engine could actually run."""
    if importlib.util.find_spec("torch") is None:
        return False
    if importlib.util.find_spec("transformers") is None:
        return False
    directory = model_dir()
    return directory.is_dir() and (directory / "config.json").exists()


def _softmax(logits):
    shifted = logits - logits.max(axis=1, keepdims=True)
    exponentials = np.exp(shifted)
    return exponentials / exponentials.sum(axis=1, keepdims=True)


def _install_logit_capture(model):
    """Capture the frame-level logits that the wrapper otherwise discards.

    The checkpoint's forward pass builds per-frame label logits and then throws
    them away, keeping only the arg-max per section. Hooking its post-processing
    call is the least invasive way to recover the probabilities, which we need
    for the per-section confidence and for the label model. If the hook cannot
    be installed the engine still works, just without either.
    """
    try:
        module = sys.modules[type(model).__module__]
        original = module.postprocess_functional_structure
        if getattr(original, "_sectionist_capture", False):
            return

        def capture(logits, config):
            try:
                _capture["function_logits"] = (
                    logits["function_logits"][0].detach().cpu().numpy().copy()
                )
                _capture["frame_rate"] = float(config.frame_rates)
            except Exception:
                _capture.clear()
            return original(logits, config)

        capture._sectionist_capture = True
        module.postprocess_functional_structure = capture
    except Exception:
        _capture.clear()


def _annotate(segments, probabilities, frame_rate, id_to_label):
    """Add the probability-based label and confidence to each segment."""
    if probabilities is None or not frame_rate:
        return segments

    annotated = []
    for segment in segments:
        start = max(0, int(round(segment["start"] * frame_rate)))
        end = min(
            len(probabilities),
            max(start + 1, int(round(segment["end"] * frame_rate))),
        )
        if end <= start:
            annotated.append(dict(segment))
            continue

        mean = probabilities[start:end].mean(axis=0)
        best = int(mean.argmax())
        item = dict(segment)
        item["label"] = id_to_label.get(best, segment["label"])
        item["confidence"] = float(mean[best])
        annotated.append(item)
    return annotated


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
        _install_logit_capture(model)

        from dataset.label2id import ID_TO_LABEL

        _models[key] = (model, dict(ID_TO_LABEL))
        return _models[key]


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

    def _infer(self, file_path):
        """Run the model once and return everything derived from that run."""
        import librosa
        import torch

        audio, _ = librosa.load(file_path, sr=SAMPLE_RATE, mono=True)
        tensor = torch.from_numpy(audio).to(self.device)

        model, id_to_label = self._model()
        with _inference_lock:
            _capture.clear()
            with torch.inference_mode():
                segments = model(tensor)
            logits = _capture.get("function_logits")
            frame_rate = _capture.get("frame_rate")
            _capture.clear()

        probabilities = _softmax(logits) if logits is not None else None
        reduced = (
            reduce_probabilities(probabilities, id_to_label)
            if probabilities is not None
            else None
        )
        return segments, probabilities, reduced, frame_rate, id_to_label

    def frame_probabilities(self, file_path):
        """Return ``(reduced_probabilities, frame_rate)`` for tooling/training."""
        _, _, reduced, frame_rate, _ = self._infer(file_path)
        return reduced, frame_rate

    def analyze(self, file_path: str) -> dict:
        # Tempo, key and chords still come from the existing pipeline.
        result = self._baseline.analyze(file_path)

        segments, probabilities, reduced, frame_rate, id_to_label = self._infer(
            file_path
        )
        annotated = _annotate(segments, probabilities, frame_rate, id_to_label)
        prepared = prepare_segments(annotated)

        model = load_label_model()
        if model is not None and reduced is not None:
            apply_calibration(prepared, reduced, frame_rate, model, result["duration"])

        sections = finalize_sections(prepared)

        downbeats = result.get("downbeats")
        if downbeats:
            sections = snap_boundaries(sections, downbeats)

        result["sections"] = sections
        result["engine"] = self.name
        return result
