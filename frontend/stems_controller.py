"""Connects the stem splitter to the main window.

The window keeps talking to ``window.audio_player`` and never needs to know
which player that is: VLC for the original file, or a StemPlayer while stems
are shown. Switching keeps the playhead where it was and carries on playing if
the song was playing.
"""

from PyQt6.QtCore import QObject
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QMessageBox, QPushButton

try:
    from .stem_player import StemPlayer, playback_available
    from .stems_client import STEM_MODELS, StemsWorker
except ImportError:
    from stem_player import StemPlayer, playback_available
    from stems_client import STEM_MODELS, StemsWorker

INSTALL_HINT = (
    "Playing stems needs the sounddevice and soundfile packages.\n"
    "Install them with: pip install -r frontend/requirements.txt"
)


class StemsController(QObject):
    def __init__(self, window, stream_factory=None):
        super().__init__(window)
        self.window = window
        self.lanes = window.stem_lanes
        self.gutter = window.timeline_gutter
        self.original_player = window.audio_player
        self.stem_player = StemPlayer(stream_factory)
        self.worker = None

        self.button = QPushButton("Split stems")
        self.button.setToolTip("Separate vocals, drums, bass and the rest")
        self.button.setEnabled(False)
        self.menu = QMenu(self.button)
        self.model_actions = []
        for model, label in STEM_MODELS:
            action = QAction(label, self.button)
            action.triggered.connect(lambda _=False, m=model: self.split(m))
            self.menu.addAction(action)
            self.model_actions.append(action)
        self.button.setMenu(self.menu)
        header = window.header.layout()
        header.insertWidget(header.indexOf(window.header.analyze_button), self.button)
        window.analysis_menu.addSeparator()
        window.analysis_menu.addMenu(self.menu).setText("Split &Stems")

        self.lanes.mix_changed.connect(self.stem_player.set_audible)
        self.lanes.seek_requested.connect(window.seek_to_position)
        self.lanes.close_requested.connect(self.use_original)
        window.timeline.position_changed.connect(self.lanes.set_position)

    @property
    def active(self):
        return self.window.audio_player is self.stem_player

    # --- song lifecycle -------------------------------------------------------

    def song_changed(self, file_path):
        """A new song (or none): drop the old stems, look for cached ones."""
        self.cancel()
        self.use_original()
        self.lanes.clear()
        self.button.setEnabled(bool(file_path))
        self.button.setText("Split stems")
        if file_path and playback_available():
            self.start(StemsWorker(file_path))

    def split(self, model):
        file_path = self.window.current_file
        if not file_path:
            return
        if not playback_available():
            QMessageBox.information(self.window, "Split stems", INSTALL_HINT)
            return
        self.use_original()
        self.lanes.show_message("Starting…")
        self.button.setEnabled(False)
        self.start(StemsWorker(file_path, model))

    def start(self, worker):
        self.cancel()
        self.worker = worker
        worker.progress.connect(self.on_progress)
        worker.finished.connect(self.on_finished)
        worker.error.connect(self.on_error)
        worker.start()

    def cancel(self):
        worker, self.worker = self.worker, None
        if worker is not None:
            for signal in (worker.progress, worker.finished, worker.error):
                signal.disconnect()
            worker.requestInterruption()

    def _current(self):
        return self.sender() is self.worker

    def on_progress(self, fraction, message):
        if not self._current():
            return
        if self.worker.model is None:
            return  # quietly loading from the cache
        self.lanes.show_message(message)
        if fraction >= 0:
            self.button.setText(f"Splitting {fraction:.0%}")
        self.window.set_status(message)

    def on_finished(self, stem_set):
        if not self._current():
            return
        asked = self.worker.model is not None
        self.worker = None
        self.button.setEnabled(True)
        self.button.setText("Split stems")
        if stem_set is None:
            if asked:
                self.lanes.clear()
            return
        self.use_stems(stem_set)
        if asked:
            self.window.set_status(f"Split into {', '.join(stem_set.names)}")

    def on_error(self, message):
        if not self._current():
            return
        asked = self.worker.model is not None
        self.worker = None
        self.button.setEnabled(True)
        self.button.setText("Split stems")
        if asked:
            self.lanes.show_message(f"Couldn't split stems: {message}")
            self.window.set_status(f"Stem splitting failed: {message}")
        else:
            self.lanes.clear()

    # --- switching players ----------------------------------------------------

    def _swap(self, player):
        old = self.window.audio_player
        if old is player:
            return
        was_playing = old.is_playing
        position = old.get_position()
        old.stop()
        self.window.audio_player = player
        player.set_position(position)
        if was_playing:
            player.play()

    def use_stems(self, stem_set):
        self.stem_player.load_stems(stem_set, self.window.current_file)
        duration = self.original_player.get_duration() or self.stem_player.duration
        self.lanes.set_stems(stem_set, duration)
        self.lanes.set_sections(self.window.timeline.sections)
        self.lanes.set_position(self.window.timeline.current_position)
        self.gutter.setVisible(True)
        self._swap(self.stem_player)

    def use_original(self):
        self._swap(self.original_player)
        self.stem_player.stop()
        self.stem_player.close()
        self.lanes.clear()
        self.gutter.setVisible(False)

    def shutdown(self):
        self.cancel()
        self.stem_player.stop()
        self.stem_player.close()
