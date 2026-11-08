"""Background stem separation jobs for the ``/stems`` endpoints.

Separation takes seconds on a GPU but minutes on a CPU, far too long to hold an
HTTP request open, so the server starts a job and the frontend polls it.
"""

import os
import threading
import time
import uuid

from . import stems as stem_separation

KEEP_JOBS = 32  # finished jobs remembered for polling and download
MAX_PENDING = 8  # queued or running; more is refused rather than piling up


class TooManyJobs(RuntimeError):
    pass


class StemJob:
    def __init__(self, model):
        self.id = uuid.uuid4().hex[:12]
        self.model = model
        self.status = "queued"  # queued, running, done, error
        self.progress = 0.0
        self.stems = {}
        self.error = None
        self.created = time.time()

    def info(self):
        return {
            "job_id": self.id,
            "model": self.model,
            "status": self.status,
            "progress": round(self.progress, 3),
            "stems": list(self.stems),
            "error": self.error,
        }


_jobs = {}
_jobs_lock = threading.Lock()


def _remember(job):
    with _jobs_lock:
        pending = [j for j in _jobs.values() if j.status in ("queued", "running")]
        if len(pending) >= MAX_PENDING:
            raise TooManyJobs("Too many stem jobs waiting; try again shortly.")
        _jobs[job.id] = job
        excess = len(_jobs) - KEEP_JOBS
        if excess > 0:
            finished = [j for j in _jobs.values() if j.status in ("done", "error")]
            finished.sort(key=lambda j: j.created)
            for old in finished[:excess]:
                del _jobs[old.id]


def get_job(job_id):
    with _jobs_lock:
        return _jobs.get(job_id)


def _run(job, file_path, separate):
    def progress(fraction):
        job.status = "running"
        job.progress = fraction

    try:
        job.stems = separate(file_path, job.model, progress=progress)
        job.progress = 1.0
        job.status = "done"
    except Exception as error:  # reported to the frontend, not raised
        job.error = str(error) or error.__class__.__name__
        job.status = "error"
    finally:
        _remove(file_path)


def _remove(path):
    try:
        os.remove(path)
    except OSError:
        pass


def start_job(file_path, model, separate=None, background=True):
    """Separate ``file_path`` (which the job deletes when done) into stems."""
    job = StemJob(model)
    try:
        _remember(job)
    except TooManyJobs:
        _remove(file_path)
        raise
    args = (job, file_path, separate or stem_separation.separate)
    if background:
        threading.Thread(target=_run, args=args, daemon=True).start()
    else:
        _run(*args)
    return job
