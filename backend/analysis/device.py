"""Device selection shared by the optional model engines."""

import os

DEVICE_ENV = "SECTIONIST_DEVICE"


def resolve_device(requested=None):
    """Pick an inference device.

    CUDA is used automatically when present. Apple's MPS is deliberately *not*
    selected automatically: it is faster on short inputs but collapses on
    longer ones on unified-memory machines (see docs/MODEL_RESEARCH.md). Set
    ``SECTIONIST_DEVICE=mps`` to opt in.
    """
    choice = (requested or os.environ.get(DEVICE_ENV, "auto") or "auto").strip().lower()
    if choice not in ("", "auto"):
        return choice

    import torch

    if torch.cuda.is_available():
        return "cuda"
    return "cpu"
