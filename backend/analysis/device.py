"""Device selection shared by the optional model engines."""

import os

DEVICE_ENV = "SECTIONIST_DEVICE"


def resolve_device(requested=None):
    """Pick an inference device.

    CUDA wins when present, then Apple's MPS, then CPU.

    MPS used to be opt-in because it collapsed on long inputs: past roughly 200
    seconds it started swapping and lost to the CPU. Long tracks are now split
    into overlapping windows (see chunking.py), which keeps each forward pass in
    MPS's fast regime, so it is a safe default again. Set
    ``SECTIONIST_DEVICE=cpu`` to override.
    """
    choice = (requested or os.environ.get(DEVICE_ENV, "auto") or "auto").strip().lower()
    if choice not in ("", "auto"):
        return choice

    import torch

    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"
