"""The window's add-ons, created together and told about the song's life.

Stems, the cycle region, locks and lyrics editing, mix export and the gig
sheet each live in their own module. The main window only calls the handful
of hooks here, so it stays a window rather than a list of features.
"""

try:
    from .cycle import CycleController
    from .gig_sheet import GigSheet
    from .mix_export import MixExporter
    from .song_edits import LockController
    from .stems_controller import StemsController
except ImportError:
    from cycle import CycleController
    from gig_sheet import GigSheet
    from mix_export import MixExporter
    from song_edits import LockController
    from stems_controller import StemsController


class Addons:
    def __init__(self, window):
        # Kept as window attributes: the add-ons reach each other this way
        # (the cycle region tells the stem player where to loop, and so on).
        window.stems = StemsController(window)
        window.cycle = CycleController(window)
        window.locks = LockController(window)
        window.mix_export = MixExporter(window)
        window.gig_sheet = GigSheet(window)
        self.window = window

    def song_changed(self, file_path):
        """A song was opened (or closed, with None)."""
        self.window.stems.song_changed(file_path)
        self.window.cycle.clear()
        self.window.locks.reset()

    def keep_locked(self, results):
        """Fresh analysis results, with anything locked kept as it was."""
        return self.window.locks.keep_locked(results)

    def analysis_finished(self, results):
        self.window.stems.analysis_finished(results.get("analysis", {}))

    def saved(self):
        """Extra state stored alongside the analysis in a saved song."""
        return {"cycle": self.window.cycle.saved(), "locks": self.window.locks.saved()}

    def song_loaded(self, results):
        """A saved song was opened: bring back its region and locks."""
        self.window.cycle.restore(results.get("cycle"))
        self.window.locks.restore(results.get("locks"))

    def shutdown(self):
        self.window.stems.shutdown()
        self.window.mix_export.shutdown()
