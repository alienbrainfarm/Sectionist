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
from .lyrics import lyrics_available, transcribe
from .stem_chords import chords_for_file


class LibrosaAnalyzer(Analyzer):
    """Heuristic segmentation plus tempo/key/chord estimation with librosa."""

    name = "librosa"

    def analyze(self, file_path: str, include_sections: bool = True) -> dict:
        """Analyse a file.

        ``include_sections=False`` skips the heuristic segmentation, which is
        wasted work when another engine will provide the sections.
        """
        # Imported lazily: example.py loads librosa and prints a banner.
        from example import analyze_audio_file

        result = analyze_audio_file(file_path, include_sections=include_sections)
        result.setdefault("engine", self.name)
        beats, downbeats = self.beat_grid(file_path)
        self.add_beats(file_path, result, beats, downbeats)
        self.add_stem_chords(file_path, result, beats, downbeats)
        self.add_lyrics(file_path, result)
        return result

    @staticmethod
    def beat_grid(file_path):
        """Beat This! beats and downbeats, or two empty lists."""
        if not beats_available():
            return [], []
        try:
            beats, downbeats = detect_beats(file_path)
        except Exception as exc:  # pragma: no cover - optional model
            print(f"Beat tracking unavailable: {exc}")
            return [], []
        return beats or [], downbeats or []

    @staticmethod
    def add_stem_chords(file_path, result, beats=None, downbeats=None):
        """Replace the mix chords with stem-based ones when stems are used.

        ``chord_source`` records which it was, so the UI can say so.
        """
        result["chord_source"] = "mix"
        try:
            chords = chords_for_file(file_path, beats, downbeats)
        except Exception as exc:  # stems are an improvement, never a failure
            print(f"Stem chords unavailable, using the mix: {exc}")
            return result
        if chords:
            duration = result.get("duration") or float("inf")
            result["chords"] = [c for c in chords if c["end"] <= duration + 0.05]
            result["chord_source"] = "stems"
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

    @staticmethod
    def add_lyrics(file_path, result, lines=None):
        """Attach transcribed lyrics to ``result``, or leave it untouched.

        ``lyrics_available`` tells the app whether there was a transcriber at
        all, so it can tell "install faster-whisper" from "no vocals found".
        """
        if lines is None:
            result["lyrics_available"] = lyrics_available()
            if not result["lyrics_available"]:
                return result
            try:
                lines = transcribe(file_path)
            except Exception as exc:  # pragma: no cover - optional model
                print(f"Lyrics transcription unavailable: {exc}")
                return result

        if lines:
            result["lyrics"] = lines
        return result
