#!/usr/bin/env python3
"""Measure SongFormer on a local audio file.

This is a research tool, not part of the application. It loads the model from a
local snapshot, segments one file and prints timing plus the detected sections.

Setup (see docs/MODEL_RESEARCH.md for the full story):

    cd backend
    python3 -m venv venv && source venv/bin/activate
    pip install -r requirements.txt -r requirements-songformer.txt
    python -c "from huggingface_hub import snapshot_download; \
        snapshot_download('ASLP-lab/SongFormer', local_dir='../.hf-cache/SongFormer')"

Usage, from the repository root:

    HF_HOME="$PWD/.hf-cache" backend/venv/bin/python \
        tools/spike_songformer.py song.mp3
    SPIKE_DEVICE=cpu ...   # or mps, cuda

Known traps: transformers 5.x breaks MuQ's constructor; the snapshot directory
must be on sys.path; msaf needs a one-line scipy patch. See the doc.
"""

import argparse
import os
import resource
import sys
import time

DEFAULT_LOCAL_DIR = os.path.join(
    os.path.dirname(__file__), "..", ".hf-cache", "SongFormer"
)


def peak_rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024**3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", help="audio file to analyse")
    parser.add_argument(
        "--model-dir",
        default=os.environ.get("SONGFORMER_LOCAL_DIR", DEFAULT_LOCAL_DIR),
        help="local snapshot directory",
    )
    parser.add_argument(
        "--device",
        default=os.environ.get("SPIKE_DEVICE", "cpu"),
        help="cpu (default), mps or cuda",
    )
    parser.add_argument("--repeat", type=int, default=2, help="timed runs")
    args = parser.parse_args()

    local_dir = os.path.abspath(args.model_dir)
    if not os.path.isdir(local_dir):
        sys.exit(f"model snapshot not found at {local_dir}")

    # The checkpoint's remote code imports its vendored siblings by bare name.
    sys.path.insert(0, local_dir)
    os.environ["SONGFORMER_LOCAL_DIR"] = local_dir

    import librosa
    import torch
    from transformers import AutoModel

    print(f"torch {torch.__version__} | device {args.device}")

    started = time.time()
    model = AutoModel.from_pretrained(
        local_dir, trust_remote_code=True, low_cpu_mem_usage=False
    )
    model.eval()
    model.to(args.device)
    print(f"model loaded in {time.time() - started:.1f}s | rss {peak_rss_gb():.2f} GB")

    audio, sr = librosa.load(args.audio, sr=24000, mono=True)
    duration = len(audio) / sr
    print(f"audio {duration:.1f}s at {sr} Hz")

    tensor = torch.from_numpy(audio).to(args.device)
    for attempt in range(1, args.repeat + 1):
        started = time.time()
        with torch.inference_mode():
            segments = model(tensor)
        elapsed = time.time() - started
        print(
            f"\nrun {attempt}: {elapsed:.1f}s "
            f"({duration / elapsed:.1f}x realtime) | rss {peak_rss_gb():.2f} GB"
        )
        for segment in segments:
            print(
                f"  {segment['start']:7.2f} - {segment['end']:7.2f}  {segment['label']}"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
