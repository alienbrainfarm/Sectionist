"""Shared types and helpers for analysis engines."""

from abc import ABC, abstractmethod


class Analyzer(ABC):
    """An audio analyser.

    ``analyze`` must return the dictionary shape the HTTP API exposes:

    ``duration``, ``tempo``, ``key``, ``key_changes``, ``sections``,
    ``beats_detected``, ``chords`` (and optionally ``engine``).
    """

    name = "base"

    @abstractmethod
    def analyze(self, file_path: str) -> dict:
        """Analyse ``file_path`` and return the result dictionary."""
