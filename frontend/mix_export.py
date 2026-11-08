"""Export a mix of the stems you can hear, as MP3 or WAV.

What is exported is what is playing: the stems left audible by mute and
solo, over the cycle region when one is active and the whole song otherwise.
A practice track without the bass, say, or a loop of the chorus without the
vocals, ready for a phone.
"""

from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QFileDialog, QMessageBox

FADE_SECONDS = 0.005  # no click where a loop is cut out of the song
HEADROOM = 0.98  # summed stems can exceed full scale; scale down if they do
MP3_BITRATE = 192


def render_mix(stem_set, names, start=None, end=None):
    """Float32 stereo samples of the named stems between two times."""
    import numpy as np

    rate = stem_set.samplerate
    first = int(round((start or 0.0) * rate))
    last = stem_set.frames if end is None else int(round(end * rate))
    first, last = max(0, first), min(stem_set.frames, last)
    mix = np.zeros((max(0, last - first), 2), dtype=np.float32)
    for name in names:
        mix += stem_set.samples[name][first:last]
    mix /= 32768.0
    peak = float(np.abs(mix).max()) if mix.size else 0.0
    if peak > HEADROOM:
        mix *= HEADROOM / peak
    # Fade only where the export cuts into the song: the song's own start and
    # end are left exactly as they are.
    fade = min(int(FADE_SECONDS * rate), len(mix) // 2)
    if fade:
        ramp = np.linspace(0.0, 1.0, fade, dtype=np.float32)[:, None]
        if first > 0:
            mix[:fade] *= ramp
        if last < stem_set.frames:
            mix[-fade:] *= ramp[::-1]
    return mix


def write_mix(samples, rate, path):
    """Write float samples as MP3 (by extension) or WAV."""
    import numpy as np

    path = Path(path)
    if path.suffix.lower() == ".mp3":
        import lameenc

        encoder = lameenc.Encoder()
        encoder.set_bit_rate(MP3_BITRATE)
        encoder.set_in_sample_rate(rate)
        encoder.set_channels(2)
        encoder.set_quality(2)  # 2 is high quality, 7 is fastest
        pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
        path.write_bytes(encoder.encode(pcm.tobytes()) + encoder.flush())
    else:
        import soundfile as sf

        sf.write(str(path), samples, rate, subtype="PCM_16")


def mp3_available():
    try:
        import lameenc  # noqa: F401
    except ImportError:
        return False
    return True


def default_name(song_path, names, all_names, region):
    """e.g. 'My Song - no vocals (0:48-1:01).mp3'."""
    title = Path(song_path).stem
    muted = [name for name in all_names if name not in names]
    if not muted:
        part = "mix"
    elif len(muted) <= len(names):
        part = "no " + " ".join(muted)
    else:
        part = " + ".join(names)
    if region is not None:

        def clock(seconds):
            return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"

        part += f" ({clock(region.start)}-{clock(region.end)})"
    return f"{title} - {part}.mp3"


class ExportWorker(QThread):
    done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, stem_set, names, start, end, path):
        super().__init__()
        self.args = (stem_set, names, start, end)
        self.path = path

    def run(self):
        try:
            stem_set = self.args[0]
            write_mix(render_mix(*self.args), stem_set.samplerate, self.path)
            self.done.emit(self.path)
        except Exception as error:
            self.failed.emit(str(error) or error.__class__.__name__)


class MixExporter(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.worker = None
        self.action = QAction("&Export Mix…", window)
        self.action.setShortcut(QKeySequence("Ctrl+E"))
        self.action.setToolTip("Save the stems you can hear as an MP3 or WAV")
        self.action.triggered.connect(self.export)
        file_menu = window.save_action.associatedObjects()[0]
        file_menu.insertAction(window.close_action, self.action)

    def selection(self):
        """(stem set, audible names, region or None) for what would export."""
        stems = self.window.stems
        if not stems.active or stems.stem_player.stem_set is None:
            return None, [], None
        region = self.window.cycle.region
        region = region if region is not None and region.enabled else None
        return stems.stem_player.stem_set, stems.lanes.audible(), region

    def export(self):
        stem_set, names, region = self.selection()
        if stem_set is None:
            QMessageBox.information(
                self.window,
                "Export Mix",
                "Exporting a mix needs the song's stems. Split stems (or wait "
                "for them to load after the analysis) and try again.",
            )
            return
        if not names:
            QMessageBox.information(
                self.window, "Export Mix", "Every stem is muted: nothing to export."
            )
            return
        song = self.window.current_file
        suggested = Path(song).with_name(
            default_name(song, names, stem_set.names, region)
        )
        filters = "MP3 audio (*.mp3);;WAV audio (*.wav)"
        if not mp3_available():
            filters = "WAV audio (*.wav)"
            suggested = suggested.with_suffix(".wav")
        path, _ = QFileDialog.getSaveFileName(
            self.window, "Export Mix", str(suggested), filters
        )
        if not path:
            return
        start, end = (region.start, region.end) if region else (None, None)
        self.window.set_status(f"Exporting {Path(path).name}…")
        self.worker = ExportWorker(stem_set, names, start, end, path)
        # Methods, not lambdas: PyQt drops a method's connection when this
        # object is destroyed, so a result arriving after the window closed
        # is ignored instead of calling into a deleted window (which aborts).
        self.worker.done.connect(self.exported)
        self.worker.failed.connect(self.export_failed)
        self.worker.start()

    def exported(self, path):
        self.window.set_status(f"Exported {Path(path).name}")

    def export_failed(self, message):
        self.window.set_status(f"Export failed: {message}")

    def shutdown(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.wait(10000)
