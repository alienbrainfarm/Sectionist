"""A small label model trained on corrected songs.

SongFormer's encoders stay frozen. Instead of retraining them, this fits a
classifier on what the network already believes about a section: the mean
probability of each structural label, plus cheap context (duration, position in
the song, whether it is first or last).

That is enough to learn systematic corrections — for example "on my library,
sections the network calls chorus at 0.7 with a pre-chorus at 0.2 are usually
pre-chorus" — without a GPU or the upstream training pipeline. It is a learned
calibration layer, not fine-tuning of SongFormer's transformer weights; see
docs/MODEL_RESEARCH.md for that distinction.
"""

import json
import re

import numpy as np

# Canonical label order used by both training and inference. Must stay in sync
# with the model's label set.
CLASS_ORDER = [
    "intro",
    "verse",
    "pre-chorus",
    "chorus",
    "bridge",
    "inst",
    "silence",
    "outro",
]

_ALIASES = {
    "instrumental": "inst",
    "prechorus": "pre-chorus",
    "pre chorus": "pre-chorus",
    "postchorus": "post-chorus",
    "post chorus": "post-chorus",
}

_TRAILING_NUMBER = re.compile(r"\s+\d+$")


def canonical_label(name):
    """Map a display name ("Verse 2", "Instrumental") to a model label."""
    text = str(name).strip().lower()
    text = _TRAILING_NUMBER.sub("", text)
    text = _ALIASES.get(text, text)
    return text


def reduce_probabilities(probabilities, id_to_label):
    """Reduce the model's 128 output classes to ``CLASS_ORDER`` columns."""
    mapping = {}
    for column, label in id_to_label.items():
        canonical = canonical_label(label)
        if canonical in CLASS_ORDER and canonical not in mapping:
            mapping[canonical] = int(column)

    reduced = np.zeros((probabilities.shape[0], len(CLASS_ORDER)))
    for index, name in enumerate(CLASS_ORDER):
        column = mapping.get(name)
        if column is not None and column < probabilities.shape[1]:
            reduced[:, index] = probabilities[:, column]

    totals = reduced.sum(axis=1, keepdims=True)
    totals[totals == 0] = 1.0
    return reduced / totals


def section_features(probabilities, frame_rate, segments, duration):
    """Build the feature matrix for a list of sections.

    Features: the eight mean label probabilities, log duration, relative
    position, normalised index, is-first and is-last.
    """
    rows = []
    count = max(1, len(segments))
    for index, segment in enumerate(segments):
        start = max(0, int(round(float(segment["start"]) * frame_rate)))
        end = min(
            len(probabilities),
            max(start + 1, int(round(float(segment["end"]) * frame_rate))),
        )
        if end <= start:
            mean = np.full(len(CLASS_ORDER), 1.0 / len(CLASS_ORDER))
        else:
            mean = probabilities[start:end].mean(axis=0)

        seconds = float(segment["end"]) - float(segment["start"])
        relative = float(segment["start"]) / duration if duration else 0.0
        rows.append(
            np.concatenate(
                [
                    mean,
                    [
                        np.log1p(max(seconds, 0.0)),
                        relative,
                        index / count,
                        1.0 if index == 0 else 0.0,
                        1.0 if index == count - 1 else 0.0,
                    ],
                ]
            )
        )
    return np.array(rows, dtype=float)


class SoftmaxRegression:
    """Multinomial logistic regression, dependency-free.

    Small enough to train on a few dozen songs in a second, and easy to inspect.
    """

    def __init__(self, l2=1e-3, learning_rate=0.5, epochs=1500):
        self.l2 = l2
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.weights = None
        self.bias = None
        self.mean = None
        self.scale = None

    def _standardise(self, features):
        return (features - self.mean) / self.scale

    def fit(self, features, targets):
        features = np.asarray(features, dtype=float)
        targets = np.asarray(targets, dtype=int)

        self.mean = features.mean(axis=0)
        self.scale = features.std(axis=0)
        self.scale[self.scale == 0] = 1.0

        standardised = self._standardise(features)
        samples, dimensions = standardised.shape
        classes = len(CLASS_ORDER)

        self.weights = np.zeros((dimensions, classes))
        self.bias = np.zeros(classes)

        one_hot = np.zeros((samples, classes))
        one_hot[np.arange(samples), targets] = 1.0

        for _ in range(self.epochs):
            logits = standardised @ self.weights + self.bias
            logits -= logits.max(axis=1, keepdims=True)
            exponentials = np.exp(logits)
            probabilities = exponentials / exponentials.sum(axis=1, keepdims=True)

            error = probabilities - one_hot
            gradient_w = standardised.T @ error / samples + self.l2 * self.weights
            gradient_b = error.mean(axis=0)

            self.weights -= self.learning_rate * gradient_w
            self.bias -= self.learning_rate * gradient_b

        return self

    def predict_proba(self, features):
        standardised = self._standardise(np.asarray(features, dtype=float))
        logits = standardised @ self.weights + self.bias
        logits -= logits.max(axis=1, keepdims=True)
        exponentials = np.exp(logits)
        return exponentials / exponentials.sum(axis=1, keepdims=True)

    def save(self, path):
        np.savez(
            path,
            weights=self.weights,
            bias=self.bias,
            mean=self.mean,
            scale=self.scale,
        )

    @classmethod
    def load(cls, path):
        data = np.load(path)
        model = cls()
        model.weights = data["weights"]
        model.bias = data["bias"]
        model.mean = data["mean"]
        model.scale = data["scale"]
        return model


def apply_calibration(segments, probabilities, frame_rate, model, duration):
    """Relabel merged segments with a trained model, in place."""
    if not segments or probabilities is None or model is None:
        return segments

    features = section_features(probabilities, frame_rate, segments, duration)
    predicted = model.predict_proba(features)

    for segment, distribution in zip(segments, predicted):
        best = int(np.argmax(distribution))
        segment["label"] = CLASS_ORDER[best]
        segment["confidence"] = float(distribution[best])
    return segments


def load_corrections(analysis_path):
    """Read the corrected sections from a saved song's ``analysis.json``."""
    with open(analysis_path, encoding="utf-8") as handle:
        payload = json.load(handle)

    analysis = payload.get("analysis", payload)
    sections = analysis.get("sections", [])
    return [
        {
            "start": float(section["start"]),
            "end": float(section["end"]),
            "label": canonical_label(section.get("name", "")),
        }
        for section in sections
        if section.get("end", 0) > section.get("start", 0)
    ]
