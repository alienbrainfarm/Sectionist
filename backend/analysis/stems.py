"""Stem separation with Demucs.

Stems serve the whole analysis whenever Demucs is installed:

- The stem splitter (``/stems`` in server.py) separates a whole song into
  vocals, drums, bass and other (plus guitar and piano with the six-stem model)
  so the frontend can mute and solo them.
- Chords are read from the accompaniment and bass stems (stem_chords.py),
  which on songs with known chords raised accuracy from 69% to 91%.
- Lyrics are transcribed from the vocal stem instead of the full mix.

Separation takes a few seconds on a GPU and roughly half the song's length on a
CPU. ``SECTIONIST_STEMS=off`` makes analysis use the mix instead; the stem
splitter still works.

Stems are cached by the file's contents, not its path: the server receives
uploads under temporary names, so a path would never match twice. A song is
only separated once per model, whichever of the two asked first.
"""

import hashlib
import importlib.util
import json
import os
import shutil
import tempfile
import threading
from pathlib import Path

STEMS_ENV = "SECTIONIST_STEMS"
CACHE_ENV = "SECTIONIST_STEMS_CACHE"
CACHE_LIMIT_ENV = "SECTIONIST_STEMS_CACHE_MB"
# A four-minute song's stems take roughly 50 MB, so this keeps ~40 songs.
DEFAULT_CACHE_MB = 2048

# Demucs models offered to the frontend, in the order they are listed there.
MODELS = {
    "htdemucs": "4 stems",
    "htdemucs_ft": "4 stems, high quality (about 4x slower)",
    "htdemucs_6s": "6 stems: adds guitar and piano",
}
DEFAULT_MODEL = "htdemucs"

# Display order; any stem a model adds that is not listed goes last.
STEM_ORDER = ("vocals", "drums", "bass", "guitar", "piano", "other")

MANIFEST = "stems.json"

_separators = {}
_separators_lock = threading.Lock()
# One separation at a time: two at once would just compete for the GPU (or
# every CPU core) and both finish later.
_run_lock = threading.Lock()


def stems_available():
    """True when Demucs is installed."""
    return importlib.util.find_spec("demucs") is not None


def enabled():
    """True when analysis should use stems: on by default if Demucs is here."""
    setting = (os.environ.get(STEMS_ENV, "on") or "on").strip().lower()
    if setting in ("0", "off", "false", "no", "never"):
        return False
    return stems_available()


def ordered(names):
    """Stem names in display order."""
    rank = {name: index for index, name in enumerate(STEM_ORDER)}
    return sorted(names, key=lambda name: (rank.get(name, len(rank)), name))


def cache_root():
    root = os.environ.get(CACHE_ENV) or Path(tempfile.gettempdir()) / "sectionist-stems"
    return Path(root)


def content_key(file_path):
    """A short hash of the file's bytes."""
    digest = hashlib.sha1()
    with open(file_path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()[:16]


def stem_folder(key, model):
    return cache_root() / f"{key}-{model}"


def cached_stems(folder):
    """{name: path} for a complete cached separation, or None."""
    manifest = Path(folder) / MANIFEST
    if not manifest.exists():
        return None
    try:
        names = json.loads(manifest.read_text(encoding="utf-8"))["stems"]
    except (OSError, ValueError, KeyError):
        return None
    paths = {name: Path(folder) / f"{name}.flac" for name in names}
    if not all(path.exists() for path in paths.values()):
        return None
    return {name: paths[name] for name in ordered(paths)}


def find_cached(key):
    """Return ``(model, {name: path})`` for the best cached separation.

    ``key`` is content_key(file); returns ``(None, None)`` when nothing is
    cached. (cached_stems takes a folder and returns only the dict.)

    The six-stem model comes first: its guitar and piano stems are harmony
    that the four-stem models leave mixed into "other".
    """
    for model in ("htdemucs_6s", "htdemucs_ft", DEFAULT_MODEL):
        found = cached_stems(stem_folder(key, model))
        if found:
            return model, found
    return None, None


def _device():
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def _separator(model):
    with _separators_lock:
        if model not in _separators:
            from demucs.api import Separator

            _separators[model] = Separator(model=model, device=_device())
        return _separators[model]


def progress_fraction(info):
    """Overall progress (0-1) from a Demucs chunk callback."""
    length = info.get("audio_length") or 0
    models = info.get("models") or 1
    if not length:
        return 0.0
    within = min(1.0, info.get("segment_offset", 0) / length)
    return min(1.0, (info.get("model_idx_in_bag", 0) + within) / models)


def separate(file_path, model=DEFAULT_MODEL, progress=None, key=None):
    """Separate a song into stems and return {name: FLAC path}.

    ``progress`` is called with a fraction between 0 and 1 as chunks finish.
    """
    if model not in MODELS:
        raise ValueError(f"Unknown stem model {model!r}")
    folder = stem_folder(key or content_key(file_path), model)
    stems = cached_stems(folder)
    if stems:
        _touch(folder)
        return stems

    import soundfile as sf

    separator = _separator(model)
    with _run_lock:
        stems = cached_stems(folder)  # another request may have finished it
        if stems:
            return stems

        def report(info):
            if progress is not None:
                progress(progress_fraction(info))

        separator.update_parameter(callback=report)
        try:
            _origin, separated = separator.separate_audio_file(Path(file_path))
        finally:
            separator.update_parameter(callback=None)

        # Write into a scratch folder and move it into place, so a crash half
        # way through never leaves a cache entry with missing stems.
        scratch = Path(tempfile.mkdtemp(dir=cache_root_ready()))
        try:
            for name, tensor in separated.items():
                samples = tensor.cpu().numpy().T.clip(-1.0, 1.0)
                sf.write(
                    scratch / f"{name}.flac",
                    samples,
                    separator.samplerate,
                    format="FLAC",
                    subtype="PCM_16",
                )
            manifest = {"stems": ordered(separated), "model": model}
            (scratch / MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
            if folder.exists():
                shutil.rmtree(folder, ignore_errors=True)
            scratch.rename(folder)
        finally:
            # Only left behind when writing failed part way.
            shutil.rmtree(scratch, ignore_errors=True)
        prune_cache(keep=folder)

    return cached_stems(folder)


def _touch(folder):
    """Mark a cache entry as recently used, so pruning keeps it."""
    try:
        os.utime(folder)
    except OSError:
        pass


def cache_limit_bytes():
    try:
        megabytes = float(os.environ.get(CACHE_LIMIT_ENV, DEFAULT_CACHE_MB))
    except ValueError:
        megabytes = DEFAULT_CACHE_MB
    return int(megabytes * 1024 * 1024)


def prune_cache(limit=None, keep=None):
    """Delete the least recently used separations until the cache fits.

    Returns the folders removed. ``keep`` is never removed.
    """
    limit = cache_limit_bytes() if limit is None else limit
    root = cache_root()
    if not root.exists():
        return []
    entries = []
    for folder in root.iterdir():
        if folder.is_dir():
            size = sum(f.stat().st_size for f in folder.iterdir() if f.is_file())
            entries.append((folder.stat().st_mtime, size, folder))
    total = sum(size for _mtime, size, _folder in entries)
    removed = []
    for _mtime, size, folder in sorted(entries):
        if total <= limit:
            break
        if keep is not None and folder == Path(keep):
            continue
        shutil.rmtree(folder, ignore_errors=True)
        total -= size
        removed.append(folder)
    return removed


def cache_root_ready():
    root = cache_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def vocals_path(file_path):
    """Return a cached path to the isolated vocal stem, or None."""
    if not enabled():
        return None
    try:
        return separate(file_path).get("vocals")
    except OSError:
        return None
