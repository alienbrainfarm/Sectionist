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


# Whisper's segments follow its 30-second windows, not the song: on a clean
# vocal stem they come back paragraph-long. Lines are rebuilt from word
# timings instead, breaking where a singer would.
MAX_LINE_CHARS = 48
PAUSE_SECONDS = 0.6


def _line(words):
    return {
        "start": round(float(words[0].start), 2),
        "end": round(float(words[-1].end), 2),
        "text": " ".join(word.word.strip() for word in words),
    }


def split_lines(words, max_chars=MAX_LINE_CHARS, pause=PAUSE_SECONDS):
    """Group timed words (``.start``, ``.end``, ``.word``) into lyric lines.

    A line ends at a pause, after a sentence once it has a few words, after a
    comma once it is getting long, or before it would pass ``max_chars``
    (a little more if the next word finishes the phrase).
    """
    lines, current = [], []
    for word in words:
        if not word.word.strip():
            continue
        if current:
            previous = current[-1].word.strip()
            length = len(" ".join(w.word.strip() for w in current + [word]))
            # A line may run a little long to finish its phrase rather than
            # leave one word stranded on the next ("breaks your" /
            # "concentration.").
            finishes = word.word.strip()[-1] in ".!?,;:"
            too_long = length > max_chars + (16 if finishes else 0)
            if (
                word.start - current[-1].end >= pause
                or too_long
                or (previous[-1] in ".!?" and len(current) >= 3)
                or (previous[-1] in ",;:" and length > max_chars * 0.6)
            ):
                lines.append(_line(current))
                current = []
        current.append(word)
    if current:
        lines.append(_line(current))
    return lines


def transcribe(file_path):
    """Return ``[{start, end, text}]`` lyric lines, or [] when unavailable."""
    if not lyrics_available():
        return []

    model = _get_model()

    # The isolated vocal stem when stems are on, otherwise the mix.
    source = vocals_path(file_path) or file_path
    segments, _info = model.transcribe(
        load_audio(source), vad_filter=False, word_timestamps=True
    )
    lines = []
    for segment in segments:
        if segment.words:
            lines.extend(split_lines(segment.words))
        elif segment.text.strip():
            lines.append(
                {
                    "start": round(float(segment.start), 2),
                    "end": round(float(segment.end), 2),
                    "text": segment.text.strip(),
                }
            )
    return lines
