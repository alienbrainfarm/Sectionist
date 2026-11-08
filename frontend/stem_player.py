"""Plays separated stems together, mixing them live.

VLC plays one file, so it cannot mute a single instrument. This player keeps
every stem in memory and sums the audible ones in the audio callback: mute and
solo take effect within one block (about 20 ms) and the stems can never drift
apart, because they are one stream.

It has the same playback methods as AudioPlayer, so the main window can swap
one for the other without knowing which it is talking to.
"""

import threading
from dataclasses import dataclass, field

# numpy and soundfile are imported where they are used, so the window (and
# its tests) start without them; they are only needed once there are stems.

BLOCK_FRAMES = 1024
PEAK_BINS = 1600


def playback_available():
    """True when numpy, soundfile and sounddevice (PortAudio) all load."""
    try:
        import numpy  # noqa: F401
        import sounddevice  # noqa: F401
        import soundfile  # noqa: F401
    except (ImportError, OSError):
        return False
    return True


@dataclass
class StemSet:
    """Decoded stems for one song: int16 samples, shape (frames, 2)."""

    samplerate: int
    samples: dict
    model: str = ""
    peaks: dict = field(default_factory=dict)

    @property
    def names(self):
        return list(self.samples)

    @property
    def frames(self):
        return max((len(data) for data in self.samples.values()), default=0)


def compute_peaks(samples, bins=PEAK_BINS):
    """Loudest sample per bin, 0-1, for drawing a waveform.

    The square root lifts quiet passages so a soft stem is still visible, while
    keeping every stem on the same scale so their levels can be compared.
    """
    import numpy as np

    if len(samples) == 0:
        return np.zeros(0, dtype=np.float32)
    mono = np.abs(samples.astype(np.int32)).max(axis=1)
    bins = max(1, min(bins, len(mono)))
    edges = np.linspace(0, len(mono), bins + 1, dtype=np.int64)
    peaks = np.maximum.reduceat(mono, edges[:-1])
    return np.sqrt(peaks / 32768.0).astype(np.float32)


def load_stem_set(paths, model=""):
    """Decode {name: audio file} into a StemSet, padded to a common length."""
    import numpy as np
    import soundfile as sf

    samples, rate = {}, None
    for name, path in paths.items():
        data, file_rate = sf.read(str(path), dtype="int16", always_2d=True)
        if rate is None:
            rate = file_rate
        elif file_rate != rate:
            raise ValueError(f"{name} is {file_rate} Hz, expected {rate} Hz")
        if data.shape[1] == 1:
            data = np.repeat(data, 2, axis=1)
        samples[name] = np.ascontiguousarray(data[:, :2])

    length = max((len(data) for data in samples.values()), default=0)
    for name, data in samples.items():
        if len(data) < length:
            samples[name] = np.pad(data, ((0, length - len(data)), (0, 0)))
    stem_set = StemSet(rate or 44100, samples, model)
    stem_set.peaks = {name: compute_peaks(data) for name, data in samples.items()}
    return stem_set


def _sounddevice_stream(samplerate, callback):
    import sounddevice as sd

    return sd.OutputStream(
        samplerate=samplerate,
        channels=2,
        dtype="float32",
        blocksize=BLOCK_FRAMES,
        callback=callback,
    )


class StemPlayer:
    """Mixes the audible stems of a StemSet to the default output device."""

    def __init__(self, stream_factory=None):
        self._stream_factory = stream_factory or _sounddevice_stream
        self._stream = None
        self._lock = threading.Lock()
        self.stem_set = None
        self.audible = set()
        self.frame = 0
        self.is_playing = False
        self.is_paused = False
        self.current_file = None
        self.duration = 0.0
        self.pending_seek = None  # AudioPlayer compatibility; seeks are exact here

    # --- loading -------------------------------------------------------------

    def load_stems(self, stem_set, source_file=None):
        self.stop()
        self.close()
        with self._lock:
            self.stem_set = stem_set
            self.audible = set(stem_set.names)
            self.frame = 0
        self.current_file = source_file
        self.duration = stem_set.frames / stem_set.samplerate

    def set_audible(self, names):
        """The stems to hear; everything else is silent."""
        with self._lock:
            self.audible = set(names)

    # --- mixing --------------------------------------------------------------

    def mix(self, frames):
        """The next ``frames`` of output, and whether the song has ended."""
        import numpy as np

        out = np.zeros((frames, 2), dtype=np.float32)
        with self._lock:
            stem_set = self.stem_set
            if stem_set is None:
                return out, True
            start = self.frame
            end = min(start + frames, stem_set.frames)
            count = end - start
            for name in self.audible:
                data = stem_set.samples.get(name)
                if data is not None and count > 0:
                    out[:count] += data[start:end]
            self.frame = end
            finished = end >= stem_set.frames
        out *= 1.0 / 32768.0
        np.clip(out, -1.0, 1.0, out=out)
        return out, finished

    def _callback(self, outdata, frames, _time, _status):
        block, finished = self.mix(frames)
        outdata[:] = block
        if finished:
            self.is_playing = False
            self.is_paused = False
            import sounddevice as sd

            raise sd.CallbackStop()

    # --- AudioPlayer interface -----------------------------------------------

    def play(self):
        if self.stem_set is None:
            return
        with self._lock:
            if self.frame >= self.stem_set.frames:
                self.frame = 0
        if self._stream is None:
            self._stream = self._stream_factory(
                self.stem_set.samplerate, self._callback
            )
        elif not self._stream.stopped:
            # A stream that ended by CallbackStop is inactive but not stopped,
            # and PortAudio will not start it again until it is.
            self._stream.stop()
        self._stream.start()
        self.is_playing = True
        self.is_paused = False

    def pause(self):
        if self.is_playing and self._stream is not None:
            self._stream.stop()
            self.is_paused = True
            self.is_playing = False

    def stop(self):
        if self._stream is not None:
            self._stream.stop()
        with self._lock:
            self.frame = 0
        self.is_playing = False
        self.is_paused = False

    def close(self):
        if self._stream is not None:
            self._stream.close()
            self._stream = None

    def set_position(self, position: float):
        if self.stem_set is None:
            return
        frame = int(max(0.0, float(position)) * self.stem_set.samplerate)
        with self._lock:
            self.frame = min(frame, self.stem_set.frames)

    def get_position(self) -> float:
        if self.stem_set is None:
            return 0.0
        return self.frame / self.stem_set.samplerate

    def get_duration(self) -> float:
        return self.duration

    def apply_pending_seek(self):
        pass
