"""Chord recognition over beat-synchronous chroma.

The previous implementation sliced the song into fixed 2-second blocks and
named each block independently, which produces a different chord every couple
of seconds regardless of the music. Two things are missing from that approach:

- **Beats.** Chords change on musical events, not on a timer.
- **Continuity.** Chords persist for bars; a decoder that cannot stay in the
  same state will jitter between adjacent templates.

This module segments at beats, scores chroma against chord templates, and runs
a Viterbi pass with a strong self-transition so a chord only changes when the
evidence actually changes. It stays dependency-free (librosa + numpy) so the
backend works without any model.

A learned model could replace this later behind the same interface.
"""

import numpy as np

PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Intervals above the root, in semitones.
QUALITIES = {
    "maj": (0, 4, 7),
    "min": (0, 3, 7),
    "7": (0, 4, 7, 10),
}

NO_CHORD = "N"


def chord_name(root, quality):
    if quality == "maj":
        return PITCH_CLASSES[root]
    if quality == "min":
        return f"{PITCH_CLASSES[root]}m"
    return f"{PITCH_CLASSES[root]}7"


def template_specs(qualities=("maj", "min", "7")):
    """``(root, intervals)`` for each template, in build_templates order."""
    return [(root, QUALITIES[q]) for q in qualities for root in range(12)]


def build_templates(qualities=("maj", "min", "7")):
    """Return ``(names, matrix)`` with one unit-length template per chord."""
    names = []
    vectors = []
    for quality in qualities:
        intervals = QUALITIES[quality]
        for root in range(12):
            vector = np.zeros(12)
            vector[[(root + interval) % 12 for interval in intervals]] = 1.0
            vectors.append(vector / np.linalg.norm(vector))
            names.append(chord_name(root, quality))
    return names, np.array(vectors)


def observation_vector(chroma_slice):
    """Mean chroma over a slice, L2-normalised. Returns None if silent."""
    mean = chroma_slice.mean(axis=1)
    norm = np.linalg.norm(mean)
    if norm < 1e-6:
        return None
    return mean / norm


def with_edges(times, duration):
    """Beat times with the start and end of the song added if missing."""
    times = np.asarray(times, dtype=float)
    if len(times) == 0 or times[0] > 0:
        times = np.concatenate([[0.0], times])
    if times[-1] < duration:
        times = np.concatenate([times, [duration]])
    return times


def beat_observations(chroma, times, sr, hop_length):
    """One normalised chroma vector (or None) per span between beat times."""
    observations = []
    for start, end in zip(times[:-1], times[1:]):
        first = int(round(start * sr / hop_length))
        last = max(first + 1, int(round(end * sr / hop_length)))
        observations.append(observation_vector(chroma[:, first:last]))
    return observations


def _frame_similarities(observations, templates):
    """Cosine similarity between each frame's chroma and every template."""
    similarities = np.zeros((len(observations), len(templates)))
    for index, observation in enumerate(observations):
        if observation is None:
            continue
        similarities[index] = templates @ observation
    return similarities


def _emission_scores(similarities, sharpness=12.0):
    """Turn similarities into log-probabilities over templates."""
    logits = sharpness * similarities
    logits -= logits.max(axis=1, keepdims=True)
    return logits - np.log(np.exp(logits).sum(axis=1, keepdims=True))


def viterbi(emissions, self_transition=0.92):
    """Decode the most likely chord sequence, favouring continuity."""
    frames, states = emissions.shape
    if frames == 0:
        return []

    switch = (1.0 - self_transition) / max(1, states - 1)
    log_stay = np.log(self_transition)
    log_switch = np.log(switch) if switch > 0 else -np.inf

    transition = np.full((states, states), log_switch)
    np.fill_diagonal(transition, log_stay)

    score = emissions[0]
    backpointer = np.zeros((frames, states), dtype=np.int16)

    for frame in range(1, frames):
        candidates = score[:, None] + transition
        best_previous = candidates.argmax(axis=0)
        backpointer[frame] = best_previous
        score = candidates[best_previous, np.arange(states)] + emissions[frame]

    path = np.zeros(frames, dtype=np.int16)
    path[-1] = int(score.argmax())
    for frame in range(frames - 1, 0, -1):
        path[frame - 1] = backpointer[frame, path[frame]]
    return path.tolist()


def confidence_of(similarities, path):
    """Template match score of the chosen chord at each frame (0-1).

    A softmax over templates was too diffuse to read: with 24 similar-looking
    templates, a clearly correct chord still scored 8%. The cosine similarity
    of the winning template is directly interpretable instead.
    """
    return [float(similarities[frame, state]) for frame, state in enumerate(path)]


def merge_runs(path, names, confidences, times, min_duration=0.3):
    """Collapse the frame path into spans, dropping very short ones."""
    spans = []
    for frame, state in enumerate(path):
        label = names[state]
        if spans and spans[-1]["name"] == label:
            spans[-1]["end_frame"] = frame
            spans[-1]["confidences"].append(confidences[frame])
        else:
            spans.append(
                {
                    "name": label,
                    "start_frame": frame,
                    "end_frame": frame,
                    "confidences": [confidences[frame]],
                }
            )

    chords = []
    for span in spans:
        start = float(times[span["start_frame"]])
        end = float(times[min(span["end_frame"] + 1, len(times) - 1)])
        if end - start < min_duration:
            continue
        chords.append(
            {
                "name": span["name"],
                "start": round(start, 2),
                "end": round(end, 2),
                "confidence": round(float(np.mean(span["confidences"])), 2),
            }
        )
    return chords


def detect_chords(y, sr, hop_length=2048, beats=None, qualities=("maj", "min")):
    """Detect a chord sequence from audio.

    ``beats`` are beat times in seconds; when omitted they are estimated here.
    ``qualities`` selects the templates to consider; triads are the default
    because adding sevenths makes the decoder label ambiguous chroma as ``7``
    chords and hold them for whole sections.

    Returns ``name``, ``start``, ``end`` and ``confidence``, where confidence is
    the template match score of the chosen chord (0-1).
    """
    import librosa

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)

    if beats is None or len(beats) < 2:
        try:
            _, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
            times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)
        except Exception:
            times = np.array([])
        if len(times) < 2:
            # Fall back to a fine grid when no beats can be found.
            times = librosa.frames_to_time(
                np.arange(0, chroma.shape[1], max(1, chroma.shape[1] // 64)),
                sr=sr,
                hop_length=hop_length,
            )
    else:
        times = np.asarray(beats, dtype=float)

    times = with_edges(times, float(librosa.get_duration(y=y, sr=sr)))
    observations = beat_observations(chroma, times, sr, hop_length)

    if not observations:
        return []

    names, templates = build_templates(qualities)
    similarities = _frame_similarities(observations, templates)
    emissions = _emission_scores(similarities)
    path = viterbi(emissions, self_transition=0.97)
    confidences = confidence_of(similarities, path)

    return merge_runs(path, names, confidences, times)
