"""The original heuristic analyser.

Wraps :func:`example.analyze_audio_file` so it matches the engine interface.
This is the always-available fallback and the source of tempo, key, beats and
chords for the other engines.
"""

from .base import Analyzer


class LibrosaAnalyzer(Analyzer):
    """Heuristic segmentation plus tempo/key/chord estimation with librosa."""

    name = "librosa"

    def analyze(self, file_path: str) -> dict:
        # Imported lazily: example.py loads librosa and prints a banner.
        from example import analyze_audio_file

        result = analyze_audio_file(file_path)
        result.setdefault("engine", self.name)
        return result
