#!/usr/bin/env python3
"""Train a label model from songs you have corrected in the app.

How corrections are captured: when you fix sections in the UI and use
"Save Song", the app writes a folder containing the audio and an
``analysis.json`` with your sections. Those folders are the training data.

The model does not touch SongFormer's weights. It learns a mapping from what
the network already believes about a section (its eight mean label
probabilities, plus duration and position) to the label you actually wanted.

Usage:

    # Look at what would be used, without training
    python tools/train_label_model.py --songs media/verified --dry-run

    # Train and write .hf-cache/label_model.npz
    python tools/train_label_model.py --songs media/verified

The backend picks the model up automatically on its next start. Set
``SECTIONIST_LABEL_MODEL`` to use a different file, or delete it to disable.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from analysis.calibration import (  # noqa: E402
    CLASS_ORDER,
    SoftmaxRegression,
    load_corrections,
    section_features,
)
from analysis.songformer_engine import (  # noqa: E402
    DEFAULT_LABEL_MODEL,
    SongFormerAnalyzer,
)

AUDIO_EXTENSIONS = {".mp3", ".wav", ".aiff", ".aif", ".m4a", ".flac", ".ogg", ".aac"}


def find_songs(root):
    """Yield (folder, analysis.json, audio file) for saved songs under root."""
    for analysis_path in sorted(Path(root).rglob("analysis.json")):
        folder = analysis_path.parent
        audio_files = [
            path
            for path in sorted(folder.iterdir())
            if path.suffix.lower() in AUDIO_EXTENSIONS and path.is_file()
        ]
        if audio_files:
            yield folder, analysis_path, audio_files[0]
        else:
            print(f"skipping {folder}: no audio file next to analysis.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--songs",
        required=True,
        help="directory to scan recursively for saved song folders",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_LABEL_MODEL),
        help="where to write the trained model",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report the dataset without training",
    )
    parser.add_argument("--device", default=None, help="cpu (default), cuda or mps")
    args = parser.parse_args()

    engine = SongFormerAnalyzer(device=args.device)
    if not engine.device:
        sys.exit("could not resolve a device")

    features = []
    targets = []
    per_song = []
    skipped = Counter()

    for folder, analysis_path, audio_path in find_songs(args.songs):
        probabilities, frame_rate = engine.frame_probabilities(str(audio_path))
        if probabilities is None or not frame_rate:
            print(f"skipping {folder}: the model did not return frame probabilities")
            continue

        sections = load_corrections(analysis_path)
        if not sections:
            print(f"skipping {folder}: no sections in analysis.json")
            continue

        # Duration comes from the analysis file; fall back to the frame count.
        with open(analysis_path, encoding="utf-8") as handle:
            payload = json.load(handle)
        analysis = payload.get("analysis", payload)
        duration = float(analysis.get("duration") or len(probabilities) / frame_rate)

        rows = section_features(probabilities, frame_rate, sections, duration)
        kept = 0
        for row, section in zip(rows, sections):
            label = section["label"]
            if label not in CLASS_ORDER:
                skipped[label] += 1
                continue
            features.append(row)
            targets.append(CLASS_ORDER.index(label))
            kept += 1

        per_song.append((folder.name, kept))
        print(f"{folder.name}: {kept} labelled sections")

    if not features:
        sys.exit(
            "no usable sections found. Correct some songs in the app, save them, "
            "and point --songs at the folder containing those song folders."
        )

    print(f"\n{len(features)} sections from {len(per_song)} songs")
    distribution = Counter(CLASS_ORDER[index] for index in targets)
    for name, count in distribution.most_common():
        print(f"  {name:<12} {count}")
    if skipped:
        print("ignored labels:", dict(skipped))

    if args.dry_run:
        print("\ndry run: nothing written")
        return 0

    if len(features) < 12:
        print(
            f"\nwarning: only {len(features)} sections. The model will fit almost "
            "anything; treat it as a placeholder until you have more."
        )

    model = SoftmaxRegression().fit(features, targets)
    accuracy = (model.predict_proba(features).argmax(axis=1) == targets).mean()
    model.save(args.out)
    print(f"\ntraining accuracy: {accuracy:.1%}")
    print(f"wrote {args.out}")
    print("restart the backend to pick it up")
    return 0


if __name__ == "__main__":
    sys.exit(main())
