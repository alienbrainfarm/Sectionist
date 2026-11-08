"""Pluggable audio analysis engines.

The HTTP contract and the frontend are independent of which engine produced a
result. Select one with ``SECTIONIST_ENGINE``:

- ``auto`` (default) — use ``songformer`` when its dependencies and weights are
  installed, otherwise fall back to ``librosa``.
- ``songformer`` — supervised segmentation. Much better sections, but needs the
  optional requirements and a model download.
- ``librosa`` — the original heuristic pipeline, always available.
"""

import os

from .librosa_engine import LibrosaAnalyzer
from .songformer_engine import SongFormerAnalyzer, songformer_available

ENGINE_ENV = "SECTIONIST_ENGINE"
DEFAULT_ENGINE = "auto"


class EngineUnavailable(RuntimeError):
    """Raised when an engine is requested but cannot be used."""


def available_engines():
    """Return the engines that can actually run in this environment."""
    engines = ["librosa"]
    if songformer_available():
        engines.append("songformer")
    return engines


def get_analyzer(name=None):
    """Return an analyser instance for ``name`` (or the configured default)."""
    requested = (
        (name or os.environ.get(ENGINE_ENV, DEFAULT_ENGINE) or "").strip().lower()
    )

    if requested in ("", "auto"):
        if songformer_available():
            return SongFormerAnalyzer()
        return LibrosaAnalyzer()

    if requested == "librosa":
        return LibrosaAnalyzer()

    if requested == "songformer":
        if not songformer_available():
            raise EngineUnavailable(
                "The songformer engine needs optional dependencies and model "
                "weights. Install backend/requirements-songformer.txt and "
                "download the checkpoint (see docs/MODEL_RESEARCH.md)."
            )
        return SongFormerAnalyzer()

    raise EngineUnavailable(
        f"Unknown engine {requested!r}. Available: {', '.join(available_engines())}"
    )


__all__ = [
    "ENGINE_ENV",
    "DEFAULT_ENGINE",
    "EngineUnavailable",
    "LibrosaAnalyzer",
    "SongFormerAnalyzer",
    "available_engines",
    "get_analyzer",
    "songformer_available",
]
