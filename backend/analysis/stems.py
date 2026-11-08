"""Optional vocal separation with Demucs.

Separating vocals before transcription should help, and it does on some
material, but the measured trade-off is unattractive enough that this is off by
default:

- Demucs runs at roughly 2.3x realtime on CPU, so a four-minute song costs about
  105 seconds of extra work, on top of the model and the transcriber.
- On the four tracks used for testing the improvement to lyrics was marginal: a
  sparse mix transcribed the same either way, and a dense mix was garbled from
  both the mix and the stem.

Enable it with ``SECTIONIST_STEMS=1`` once Demucs is installed. Results are
cached per file under the temporary directory, so repeated analyses of the same
song only pay for separation once.
"""

import hashlib
import importlib.util
import os
import tempfile
import threading
from pathlib import Path

STEMS_ENV = "SECTIONIST_STEMS"

_separator = None
_lock = threading.Lock()


def stems_available():
    """True when Demucs is installed."""
    return importlib.util.find_spec("demucs") is not None


def enabled():
    """True when separation is switched on and possible."""
    setting = (os.environ.get(STEMS_ENV, "off") or "off").strip().lower()
    if setting not in ("1", "on", "true", "yes", "auto"):
        return False
    return stems_available()


def _device():
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def _separator_instance():
    global _separator
    with _lock:
        if _separator is None:
            from demucs.api import Separator

            _separator = Separator(model="htdemucs", device=_device())
        return _separator


def vocals_path(file_path):
    """Return a cached path to the isolated vocal stem, or None."""
    if not enabled():
        return None

    import soundfile as sf

    try:
        stamp = os.path.getmtime(file_path)
    except OSError:
        return None

    key = hashlib.sha1(f"{file_path}:{stamp}".encode()).hexdigest()[:16]
    cache = Path(tempfile.gettempdir()) / "sectionist-stems"
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / f"{key}-vocals.wav"
    if destination.exists():
        return destination

    separator = _separator_instance()
    with _lock:
        _origin, stems = separator.separate_audio_file(file_path)
        samples = stems["vocals"].cpu().numpy().T
        sf.write(destination, samples.astype("float32"), separator.samplerate)

    return destination
