"""Chord recognition from separated stems, anchored on the bass.

The mix-based detector in chords.py hears everything at once. Two things in a
mix mislead chroma more than anything else:

- **Drums** spread broadband energy across every pitch class.
- **The vocal melody** sings passing notes, suspensions and extensions that
  are not in the chord, often louder than the accompaniment.

With stems, harmony evidence comes from the accompaniment alone ("other", plus
guitar and piano from the six-stem model), and the bass stem says which note is
underneath. The bass note on the beat, and especially on the downbeat, is the
strongest single cue to the chord's root: it separates relative pairs such as
C and Am, or G and Em, which share two of their three notes and look almost the
same to chroma. When the bass sits on another chord tone instead, the chord is
named as an inversion, e.g. ``C/E``.

The bass is a bonus in each beat's score rather than a rule, so walking lines,
approach notes and rests do not force a chord change.
"""

import numpy as np

from . import stems as stem_separation
from .chords import (
    PITCH_CLASSES,
    _emission_scores,
    _frame_similarities,
    beat_observations,
    build_templates,
    confidence_of,
    merge_runs,
    template_specs,
    viterbi,
    with_edges,
)

HARMONY_STEMS = ("other", "guitar", "piano")
HOP = 512
BASS_FMIN = 41.2  # E1, the lowest string of a four-string bass
BASS_OCTAVES = 3
# Harmonics of a bass note, in semitones above it, and how much each counts
# towards that note being the fundamental. Without this the strong 3rd
# harmonic would vote for the fifth.
HARMONICS = ((0, 1.0), (12, 0.6), (19, 0.45), (24, 0.35))


def bass_salience(y_bass, sr, hop_length=HOP):
    """(12, frames) pitch-class salience of the bass fundamental, and loudness.

    Each candidate note collects its own energy plus that of its harmonics, so
    the fundamental wins over its overtones. Only the lowest two octaves are
    candidates; the third octave supplies the harmonics.
    """
    import librosa

    bins = 12 * BASS_OCTAVES
    magnitude = np.abs(
        librosa.cqt(
            y_bass,
            sr=sr,
            hop_length=hop_length,
            fmin=BASS_FMIN,
            n_bins=bins,
            bins_per_octave=12,
        )
    )
    candidates = 24
    salience = np.zeros((candidates, magnitude.shape[1]))
    for offset, weight in HARMONICS:
        top = min(candidates, bins - offset)
        salience[:top] += weight * magnitude[offset : offset + top]

    pitch_classes = np.zeros((12, magnitude.shape[1]))
    for index in range(candidates):
        # CQT bin 0 is E (pitch class 4).
        pitch_classes[(index + 4) % 12] += salience[index]
    loudness = magnitude[:candidates].sum(axis=0)
    return pitch_classes, loudness


def bass_per_beat(salience, loudness, times, sr, hop_length=HOP, attack=0.6):
    """Bass pitch-class distribution and strength for each beat.

    Only the first part of each beat counts: a bass note is played on the
    beat, and the tail of a beat often slides into the next note.
    Strength is 0 for silence and reaches 1 at a typically loud bass note.
    """
    reference = np.percentile(loudness, 90) if loudness.size else 0.0
    distributions, strengths = [], []
    for start, end in zip(times[:-1], times[1:]):
        first = int(round(start * sr / hop_length))
        last = int(round((start + attack * (end - start)) * sr / hop_length))
        last = max(first + 1, last)
        window = salience[:, first:last]
        total = window.sum()
        if total <= 1e-9 or reference <= 0:
            distributions.append(np.zeros(12))
            strengths.append(0.0)
            continue
        distribution = window.sum(axis=1) / total
        # Sharpen: the fundamental should dominate a single beat.
        distribution = distribution**2
        distributions.append(distribution / distribution.sum())
        level = loudness[first:last].mean() / reference
        strengths.append(float(np.clip(level, 0.0, 1.0)))
    return np.array(distributions), np.array(strengths)


def bass_scores(distributions, strengths, specs, downbeat_mask, downbeat_boost=1.5):
    """(beats, templates): how well each chord fits the bass on each beat.

    The root scores fully, the other chord tones a little (inversions), and
    a bass note outside the chord counts against it.
    """
    scores = np.zeros((len(distributions), len(specs)))
    for index, (root, intervals) in enumerate(specs):
        tones = [(root + interval) % 12 for interval in intervals]
        others = [tone for tone in range(12) if tone not in tones]
        scores[:, index] = (
            distributions[:, root]
            + 0.35 * distributions[:, tones[1:]].sum(axis=1)
            - 0.5 * distributions[:, others].sum(axis=1)
        )
    weight = strengths * np.where(downbeat_mask, downbeat_boost, 1.0)
    return scores * weight[:, None]


def downbeat_flags(times, downbeats, tolerance=0.07):
    """True for each beat span that starts on a downbeat."""
    if not downbeats:
        return np.zeros(len(times) - 1, dtype=bool)
    downbeats = np.asarray(downbeats, dtype=float)
    starts = np.asarray(times[:-1])
    nearest = np.abs(starts[:, None] - downbeats[None, :]).min(axis=1)
    return nearest <= tolerance


def slash_names(chords, times, path, specs, names, distributions, strengths):
    """Rename chords whose bass sits on a chord tone other than the root."""
    spans, start = [], 0
    for frame in range(1, len(path) + 1):
        if frame == len(path) or path[frame] != path[start]:
            spans.append((start, frame, path[start]))
            start = frame
    lookup = {}
    for first, last, state in spans:
        mass = (distributions[first:last] * strengths[first:last, None]).sum(axis=0)
        if mass.sum() <= 1e-9:
            continue
        mass = mass / mass.sum()
        root, intervals = specs[state]
        bass = int(mass.argmax())
        tones = [(root + interval) % 12 for interval in intervals[1:]]
        if bass in tones and mass[bass] > 0.45 and mass[bass] > 1.5 * mass[root]:
            key = round(float(times[first]), 2)
            lookup[key] = f"{names[state]}/{PITCH_CLASSES[bass]}"
    for chord in chords:
        chord["name"] = lookup.get(chord["start"], chord["name"])
    return chords


def detect_chords_from_stems(
    harmony,
    bass,
    sr,
    beats,
    downbeats=None,
    hop_length=HOP,
    qualities=("maj", "min"),
    bass_weight=4.0,
    sharpness=12.0,
    self_transition=0.97,
    slash=True,
):
    """Chords from a harmony signal and a bass signal (mono, same rate).

    ``beats`` and ``downbeats`` are times in seconds. Returns the same shape as
    chords.detect_chords: ``name``, ``start``, ``end`` and ``confidence``.
    """
    import librosa

    duration = len(harmony) / sr
    times = with_edges(beats if beats is not None else [], duration)
    if len(times) < 3:
        return []

    chroma = librosa.feature.chroma_cqt(y=harmony, sr=sr, hop_length=hop_length)
    observations = beat_observations(chroma, times, sr, hop_length)
    names, templates = build_templates(qualities)
    specs = template_specs(qualities)
    similarities = _frame_similarities(observations, templates)

    emissions = sharpness * similarities
    if bass is not None and bass_weight:
        salience, loudness = bass_salience(bass, sr, hop_length)
        distributions, strengths = bass_per_beat(
            salience, loudness, times, sr, hop_length
        )
        flags = downbeat_flags(times, downbeats)
        emissions = emissions + bass_weight * bass_scores(
            distributions, strengths, specs, flags
        )
    # Normalise per beat as the mix detector does.
    emissions = _emission_scores(emissions, sharpness=1.0)
    path = viterbi(emissions, self_transition=self_transition)
    chords = merge_runs(path, names, confidence_of(similarities, path), times)
    if slash and bass is not None and bass_weight:
        chords = slash_names(
            chords, times, path, specs, names, distributions, strengths
        )
    return chords


# --- choosing and loading stems for a file -------------------------------------


def stems_for_chords(file_path):
    """Stems to read chords from, or None to use the mix.

    Prefers a separation that is already cached (the six-stem one has the most
    harmony to read), and otherwise separates with the default model.
    """
    if not stem_separation.enabled():
        return None
    key = stem_separation.content_key(file_path)
    _model, cached = stem_separation.find_cached(key)
    return cached or stem_separation.separate(file_path, key=key)


def chords_for_file(file_path, beats=None, downbeats=None, sr=22050):
    """Chords from the file's stems, or None when stems are not used."""
    import librosa

    paths = stems_for_chords(file_path)
    if not paths or "bass" not in paths:
        return None

    def load(name):
        return librosa.load(str(paths[name]), sr=sr, mono=True)[0]

    harmony = sum(load(name) for name in HARMONY_STEMS if name in paths)
    bass = load("bass")
    if beats is None or len(beats) < 2:
        drums = load("drums") if "drums" in paths else harmony + bass
        _tempo, frames = librosa.beat.beat_track(y=drums, sr=sr, hop_length=HOP)
        beats = librosa.frames_to_time(frames, sr=sr, hop_length=HOP)
    return detect_chords_from_stems(harmony, bass, sr, beats, downbeats)
