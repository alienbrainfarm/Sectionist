"""The original heuristic analyser.

Wraps :func:`example.analyze_audio_file` so it matches the engine interface.
This is the always-available fallback and the source of tempo, key, beats and
chords for the other engines.

When Beat This! is installed it also supplies the beat count and the downbeat
grid, which the UI draws as bar lines and the model engine uses to snap
section boundaries.
"""

from .base import Analyzer
from .beats import beats_available, detect_beats


class LibrosaAnalyzer(Analyzer):
    """Heuristic segmentation plus tempo/key/chord estimation with librosa."""

    name = "librosa"

    def analyze(self, file_path: str) -> dict:
        # Imported lazily: example.py loads librosa and prints a banner.
        from example import analyze_audio_file

        result = analyze_audio_file(file_path)
        result.setdefault("engine", self.name)
        self.add_beats(file_path, result)
        return result

    @staticmethod
    def add_beats(file_path, result, beats=None, downbeats=None):
        """Attach Beat This! output to ``result``, or leave it untouched."""
        if beats is None and downbeats is None:
            if not beats_available():
                return result
            try:
                beats, downbeats = detect_beats(file_path)
            except Exception as exc:  # pragma: no cover - optional model
                print(f"Beat tracking unavailable: {exc}")
                return result

        if beats:
            result["beats_detected"] = len(beats)
        if downbeats:
            result["downbeats"] = [round(float(time), 2) for time in downbeats]
        return result
