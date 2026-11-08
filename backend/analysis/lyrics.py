"""Lyrics transcription with faster-whisper (optional).

Whisper was trained for speech, so two adjustments matter for songs:

- **Voice activity detection is off.** faster-whisper's VAD is tuned for speech
  and discards singing over a backing track; with it on, two of the test tracks
  produced no lyrics at all.
- **The vocal stem is transcribed when there is one.** With Demucs installed
  (stems.py), Whisper hears the isolated vocals instead of the band; without
  it, or with ``SECTIONIST_STEMS=off``, it transcribes the mix, which the
  `small` model copes with on vocals-forward material.

Quality depends heavily on the mix: a sparse arrangement transcribes closely,
dense productions produce approximate lines. Bigger models help and are a
setting away.
"""

import importlib.util
import os
import threading

from .stems import vocals_path

MODEL_ENV = "SECTIONIST_WHISPER_MODEL"
DEVICE_ENV = "SECTIONIST_WHISPER_DEVICE"

# `small` is the smallest model that produced usable lyrics on the test tracks.
DEFAULT_MODEL = "small"

_model = None
_model_key = None
_lock = threading.Lock()


def lyrics_available():
    """True when faster-whisper is installed."""
    return importlib.util.find_spec("faster_whisper") is not None


def _resolve_device():
    choice = (os.environ.get(DEVICE_ENV, "auto") or "auto").strip().lower()
    if choice not in ("", "auto"):
        return choice
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    # CTranslate2 has no Metal backend, so Apple Silicon uses the CPU here.
    return "cpu"


def _get_model():
    global _model, _model_key
    name = os.environ.get(MODEL_ENV, DEFAULT_MODEL)
    device = _resolve_device()
    key = (name, device)

    with _lock:
        if _model is None or _model_key != key:
            from faster_whisper import WhisperModel

            compute = "float16" if device in ("cuda", "float16") else "int8"
            _model = WhisperModel(name, device=device, compute_type=compute)
            _model_key = key
        return _model


def load_audio(path, sr=16000):
    """Mono float32 samples at Whisper's rate.

    Decoded here with librosa rather than by faster-whisper, which uses PyAV:
    faster-whisper 1.2 calls an av.open() argument that PyAV 19 removed, so
    letting it decode broke lyrics outright on a fresh install.
    """
    import librosa

    samples, _rate = librosa.load(str(path), sr=sr, mono=True)
    return samples


def transcribe(file_path):
    """Return ``[{start, end, text}]`` lyric lines, or [] when unavailable."""
    if not lyrics_available():
        return []

    model = _get_model()

    # The isolated vocal stem when stems are on, otherwise the mix.
    source = vocals_path(file_path) or file_path
    segments, _info = model.transcribe(load_audio(source), vad_filter=False)
    return [
        {
            "start": round(float(segment.start), 2),
            "end": round(float(segment.end), 2),
            "text": segment.text.strip(),
        }
        for segment in segments
        if segment.text.strip()
    ]
