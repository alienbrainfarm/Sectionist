"""Beat and downbeat detection with Beat This! (optional).

Beat This! is deliberately not a madmom-based tracker: madmom's dynamic
Bayesian network post-processing is patented and non-commercial, whereas this
model reaches state of the art with plain peak picking, and both its code and
weights are MIT.

Used for two things: reporting the beat count, and snapping section boundaries
onto downbeats so sections line up with bars.
"""

import importlib.util
import threading

from .device import resolve_device

_tracker = None
_lock = threading.Lock()


def beats_available():
    """True when Beat This! and its dependencies are installed."""
    return (
        importlib.util.find_spec("beat_this") is not None
        and importlib.util.find_spec("torch") is not None
    )


def _get_tracker(device):
    global _tracker
    with _lock:
        if _tracker is None:
            from beat_this.inference import File2Beats

            # dbn=False keeps madmom (and its patent) out of the pipeline.
            _tracker = File2Beats(checkpoint_path="final0", device=device, dbn=False)
        return _tracker


def detect_beats(file_path, device=None):
    """Return ``(beats, downbeats)`` as lists of seconds.

    Returns ``(None, None)`` when Beat This! is not installed, so callers can
    degrade gracefully.
    """
    if not beats_available():
        return None, None

    tracker = _get_tracker(device or resolve_device())
    beats, downbeats = tracker(file_path)
    return [float(t) for t in beats], [float(t) for t in downbeats]
