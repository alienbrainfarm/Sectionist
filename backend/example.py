#!/usr/bin/env python3
"""
Sectionist Backend - Song Structure Segmentation Prototype

This script demonstrates advanced audio analysis functionality that will be used
by the Sectionist macOS app for intelligent song section detection, key detection,
and basic chord mapping.

Key Features:
- Music Information Retrieval-based song structure segmentation
- Frame-based boundary detection using chroma, energy, and spectral features
- Intelligent section labeling with confidence scores
- Support for various audio formats (mp3, wav, flac, etc.)

The segmentation algorithm works by:
1. Extracting musical features (chroma, RMS energy, spectral centroid)
2. Using sliding window analysis to detect significant changes
3. Applying heuristic labeling based on position and musical characteristics
4. Providing confidence scores for each detected section
"""

import os
import sys
import numpy as np

# Note: scipy imports available for advanced processing if needed
# from scipy import ndimage, signal

try:
    import librosa

    print("✅ librosa imported successfully")
except ImportError:
    print("❌ librosa not available. Run: pip install -r requirements.txt")
    sys.exit(1)


def analyze_song_structure(y, sr):
    """
    Analyze song structure using music information retrieval techniques.

    This function implements a prototype segmentation algorithm that:
    1. Uses frame-based analysis with fixed time windows
    2. Extracts chroma and energy features
    3. Detects boundaries based on feature changes
    4. Labels segments based on musical characteristics

    Args:
        y (np.array): Audio time series
        sr (int): Sample rate

    Returns:
        list: List of detected sections with labels and timestamps
    """
    duration = librosa.get_duration(y=y, sr=sr)

    # Use fixed hop_length for consistent analysis
    hop_length = 2048  # ~0.09 seconds at 22050 Hz
    frame_times = librosa.frames_to_time(
        np.arange(len(y) // hop_length + 1), sr=sr, hop_length=hop_length
    )

    # Extract chroma features (harmonic content)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop_length)

    # Extract RMS energy
    rms = librosa.feature.rms(y=y, hop_length=hop_length)

    # Extract spectral centroid (brightness)
    spectral_centroid = librosa.feature.spectral_centroid(
        y=y, sr=sr, hop_length=hop_length
    )

    # Detect boundaries using direct frame-based analysis
    boundary_times = detect_boundaries_frame_based(
        chroma, rms, spectral_centroid, frame_times, duration
    )

    # Label sections based on their characteristics
    sections = label_sections_frame_based(
        boundary_times, chroma, rms, spectral_centroid, frame_times
    )

    return sections


def detect_boundaries_frame_based(
    chroma, rms, spectral_centroid, frame_times, duration
):
    """
    Detect boundaries using frame-based analysis with time windows.
    """
    if chroma.shape[1] < 32:  # Too few frames for analysis
        # Return basic sectioning
        return np.array([0, duration / 4, duration / 2, 3 * duration / 4, duration])

    # Use time-based windows (approximately every 5 seconds)
    window_duration = 5.0  # seconds
    frames_per_window = int(window_duration / (frame_times[1] - frame_times[0]))

    boundaries = [0]  # Always start with 0

    # Look for significant changes in features every ~2 seconds
    step_duration = 2.0
    frames_per_step = int(step_duration / (frame_times[1] - frame_times[0]))

    for i in range(
        frames_per_window, chroma.shape[1] - frames_per_window, frames_per_step
    ):
        # Compare features before and after this point
        before_chroma = chroma[:, max(0, i - frames_per_window) : i]
        after_chroma = chroma[:, i : min(chroma.shape[1], i + frames_per_window)]

        before_rms = rms[:, max(0, i - frames_per_window) : i]
        after_rms = rms[:, i : min(rms.shape[1], i + frames_per_window)]

        before_centroid = spectral_centroid[:, max(0, i - frames_per_window) : i]
        after_centroid = spectral_centroid[
            :, i : min(spectral_centroid.shape[1], i + frames_per_window)
        ]

        # Calculate differences
        if (
            before_chroma.size > 0
            and after_chroma.size > 0
            and before_rms.size > 0
            and after_rms.size > 0
        ):

            chroma_diff = np.linalg.norm(
                np.mean(before_chroma, axis=1) - np.mean(after_chroma, axis=1)
            )
            energy_diff = abs(np.mean(before_rms) - np.mean(after_rms))
            brightness_diff = abs(np.mean(before_centroid) - np.mean(after_centroid))

            # Combined score for boundary strength
            boundary_score = chroma_diff + energy_diff * 5 + brightness_diff / 1000

            # If there's a significant change, mark as boundary
            if boundary_score > 0.3:  # Adjusted threshold
                boundary_time = (
                    frame_times[i] if i < len(frame_times) else frame_times[-1]
                )
                boundaries.append(boundary_time)

    # Always end with full duration
    boundaries.append(duration)

    # Remove boundaries that are too close together (min 12 seconds apart)
    min_section_length = 12.0
    filtered_boundaries = [boundaries[0]]
    for boundary in boundaries[1:]:
        if boundary - filtered_boundaries[-1] >= min_section_length:
            filtered_boundaries.append(boundary)

    # Ensure we have the end boundary
    if filtered_boundaries[-1] != duration:
        filtered_boundaries.append(duration)

    # If we have too few sections, add some basic ones
    if len(filtered_boundaries) < 3:
        filtered_boundaries = [0, duration / 3, 2 * duration / 3, duration]

    return np.array(filtered_boundaries)


def label_sections_frame_based(
    boundary_times, chroma, rms, spectral_centroid, frame_times
):
    """
    Label sections using frame-based feature analysis.
    """
    sections = []
    total_duration = boundary_times[-1]

    for i in range(len(boundary_times) - 1):
        start_time = boundary_times[i]
        end_time = boundary_times[i + 1]
        duration = end_time - start_time
        position_ratio = start_time / total_duration if total_duration > 0 else 0

        # Find corresponding frame indices for feature analysis
        start_frame = np.argmin(np.abs(frame_times - start_time))
        end_frame = np.argmin(np.abs(frame_times - end_time))

        # Extract features for this segment
        if end_frame > start_frame and start_frame < chroma.shape[1]:
            segment_chroma = chroma[:, start_frame : min(end_frame, chroma.shape[1])]
            segment_rms = rms[:, start_frame : min(end_frame, rms.shape[1])]
            segment_centroid = spectral_centroid[
                :, start_frame : min(end_frame, spectral_centroid.shape[1])
            ]

            # Calculate characteristics
            energy_level = float(np.mean(segment_rms)) if segment_rms.size > 0 else 0.3
            chroma_stability = (
                1.0 / (1.0 + np.var(segment_chroma)) if segment_chroma.size > 0 else 0.5
            )
            brightness = (
                float(np.mean(segment_centroid)) if segment_centroid.size > 0 else 1000
            )
        else:
            energy_level = 0.3
            chroma_stability = 0.5
            brightness = 1000

        # Enhanced labeling heuristics
        if position_ratio < 0.15:
            label = "Intro"
        elif position_ratio > 0.85:
            label = "Outro"
        elif energy_level > 0.4 and brightness > 1200:
            label = "Chorus"
        elif position_ratio < 0.5:
            verse_num = min(i + 1, 3)  # Verse 1, 2, or 3
            label = f"Verse {verse_num}"
        elif duration < 20.0 and chroma_stability < 0.3:
            label = "Bridge"
        else:
            label = "Chorus" if energy_level > 0.35 else "Verse"

        sections.append(
            {
                "name": label,
                "start": round(float(start_time), 2),
                "end": round(float(end_time), 2),
                "confidence": round(float(chroma_stability), 2),
            }
        )

    return sections


def detect_key_and_changes(y, sr, chroma=None):
    """
    Detect the key and key changes throughout an audio file.

    This function implements enhanced key detection using the Krumhansl-Schmuckler
    key-finding algorithm with comprehensive key profiles for all 24 major and
    minor keys.

    Args:
        y (np.array): Audio time series
        sr (int): Sample rate
        chroma (np.array, optional): Pre-computed chroma features

    Returns:
        tuple: (detected_key, key_changes)
            - detected_key (str): Overall key of the song
            - key_changes (list): List of key changes with timestamps
    """
    # Compute chroma features if not provided
    if chroma is None:
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)

    # Krumhansl-Schmuckler key profiles (24 keys: 12 major + 12 minor)
    # Major key profiles based on probe tone experiments
    major_profile = np.array(
        [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    )

    # Minor key profiles based on probe tone experiments
    minor_profile = np.array(
        [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    )

    # Generate all 24 key profiles by rotating the base profiles
    key_profiles = []
    key_names = []

    # Major keys
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    for i in range(12):
        key_profiles.append(np.roll(major_profile, i))
        key_names.append(f"{note_names[i]} major")

    # Minor keys
    for i in range(12):
        key_profiles.append(np.roll(minor_profile, i))
        key_names.append(f"{note_names[i]} minor")

    key_profiles = np.array(key_profiles)

    # Detect overall key using entire chroma
    chroma_mean = np.mean(chroma, axis=1)
    # Normalize chroma vector
    chroma_mean = (
        chroma_mean / np.sum(chroma_mean) if np.sum(chroma_mean) > 0 else chroma_mean
    )

    # Calculate correlation with each key profile
    key_scores = []
    for profile in key_profiles:
        # Normalize key profile
        profile_norm = profile / np.sum(profile)
        # Calculate Pearson correlation coefficient
        correlation = np.corrcoef(chroma_mean, profile_norm)[0, 1]
        key_scores.append(correlation if not np.isnan(correlation) else 0)

    overall_key_idx = np.argmax(key_scores)
    detected_key = key_names[overall_key_idx]

    # Detect key changes by analyzing segments
    key_changes = detect_key_changes_in_segments(chroma, key_profiles, key_names, sr)

    return detected_key, key_changes


def detect_key_changes_in_segments(chroma, key_profiles, key_names, sr):
    """
    Detect key changes by analyzing audio in segments.

    Args:
        chroma (np.array): Chroma features
        key_profiles (np.array): All 24 key profiles
        key_names (list): Names of all keys
        sr (int): Sample rate

    Returns:
        list: List of key changes with timestamps
    """
    # Calculate segment duration (~10 seconds per segment)
    hop_length = 2048  # Standard hop length used in chroma calculation
    frames_per_second = sr / hop_length
    segment_duration_seconds = 10.0
    segment_size = int(segment_duration_seconds * frames_per_second)

    if chroma.shape[1] < segment_size * 2:  # Need at least 2 segments
        return []

    key_changes = []
    previous_key = None

    # Analyze segments
    for start_frame in range(0, chroma.shape[1] - segment_size, segment_size // 2):
        end_frame = min(start_frame + segment_size, chroma.shape[1])
        segment_chroma = chroma[:, start_frame:end_frame]

        # Calculate mean chroma for this segment
        segment_chroma_mean = np.mean(segment_chroma, axis=1)
        segment_chroma_mean = (
            segment_chroma_mean / np.sum(segment_chroma_mean)
            if np.sum(segment_chroma_mean) > 0
            else segment_chroma_mean
        )

        # Find best matching key for this segment
        segment_key_scores = []
        for profile in key_profiles:
            profile_norm = profile / np.sum(profile)
            correlation = np.corrcoef(segment_chroma_mean, profile_norm)[0, 1]
            segment_key_scores.append(correlation if not np.isnan(correlation) else 0)

        segment_key_idx = np.argmax(segment_key_scores)
        segment_key = key_names[segment_key_idx]

        # Check for key change
        if previous_key is not None and segment_key != previous_key:
            # Only report significant key changes (confidence threshold)
            confidence = segment_key_scores[segment_key_idx]
            if confidence > 0.3:  # Threshold for confident key detection
                timestamp = start_frame * hop_length / sr
                key_changes.append(
                    {
                        "timestamp": round(float(timestamp), 2),
                        "from_key": previous_key,
                        "to_key": segment_key,
                        "confidence": round(float(confidence), 2),
                    }
                )

        previous_key = segment_key

    return key_changes


def detect_chords(y, sr, hop_length=2048):
    """
    Detect basic chord progressions throughout an audio file.

    This function uses chroma features to identify major and minor chords
    by comparing the harmonic content to known chord templates.

    Args:
        y (np.array): Audio time series
        sr (int): Sample rate
        hop_length (int): Hop length for feature extraction

    Returns:
        list: List of chord progressions with timestamps
            Each chord contains:
            - name: Chord name (e.g., "C major", "Am", "F")
            - start: Start time in seconds
            - end: End time in seconds
            - confidence: Detection confidence (0-1)
    """
    # Extract chroma features
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop_length)

    # Define chord templates for major and minor chords
    # Each template is a 12-element vector representing chroma bins
    # (C, C#, D, D#, E, F, F#, G, G#, A, A#, B)
    chord_templates = {
        # Major chords
        "C": np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0]),
        "C#": np.array([0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0]),
        "D": np.array([0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0]),
        "D#": np.array([0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0]),
        "E": np.array([0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1]),
        "F": np.array([1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0]),
        "F#": np.array([0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0]),
        "G": np.array([0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1]),
        "G#": np.array([1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0]),
        "A": np.array([0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0]),
        "A#": np.array([0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0]),
        "B": np.array([0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1]),
        # Minor chords
        "Cm": np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0]),
        "C#m": np.array([0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]),
        "Dm": np.array([0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0]),
        "D#m": np.array([0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0]),
        "Em": np.array([0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1]),
        "Fm": np.array([1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0]),
        "F#m": np.array([0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0]),
        "Gm": np.array([0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0]),
        "G#m": np.array([0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1]),
        "Am": np.array([1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0]),
        "A#m": np.array([0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]),
        "Bm": np.array([0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1]),
    }

    # Calculate time frames
    frame_times = librosa.frames_to_time(
        np.arange(chroma.shape[1]), sr=sr, hop_length=hop_length
    )

    # Analyze chords in segments (every 2 seconds)
    segment_duration = 2.0  # seconds
    frames_per_segment = int(segment_duration * sr / hop_length)

    detected_chords = []

    for start_frame in range(
        0, chroma.shape[1] - frames_per_segment, frames_per_segment
    ):
        end_frame = min(start_frame + frames_per_segment, chroma.shape[1])
        segment_chroma = chroma[:, start_frame:end_frame]

        # Calculate mean chroma for this segment
        mean_chroma = np.mean(segment_chroma, axis=1)

        # Normalize chroma vector
        if np.sum(mean_chroma) > 0:
            mean_chroma = mean_chroma / np.sum(mean_chroma)

        # Find best matching chord
        best_chord = "N"  # No chord detected
        best_score = 0

        for chord_name, template in chord_templates.items():
            # Calculate cosine similarity between mean_chroma and template
            # Normalize vectors
            chroma_norm = np.linalg.norm(mean_chroma)
            template_norm_val = np.linalg.norm(template)

            if chroma_norm > 0 and template_norm_val > 0:
                # Cosine similarity
                score = np.dot(mean_chroma, template) / (
                    chroma_norm * template_norm_val
                )
            else:
                score = 0

            if score > best_score:
                best_score = score
                best_chord = chord_name

        # Only include chord if confidence is above threshold
        confidence_threshold = 0.3  # Lowered from 0.5 for better detection
        if best_score > confidence_threshold:
            start_time = (
                frame_times[start_frame]
                if start_frame < len(frame_times)
                else frame_times[-1]
            )
            end_time = (
                frame_times[end_frame - 1]
                if end_frame - 1 < len(frame_times)
                else frame_times[-1]
            )

            detected_chords.append(
                {
                    "name": best_chord,
                    "start": round(float(start_time), 2),
                    "end": round(float(end_time), 2),
                    "confidence": round(float(best_score), 2),
                }
            )

    # Post-process to merge consecutive identical chords
    if detected_chords:
        merged_chords = [detected_chords[0]]

        for chord in detected_chords[1:]:
            last_chord = merged_chords[-1]
            # If same chord and consecutive time segments, merge them
            if (
                chord["name"] == last_chord["name"]
                and abs(chord["start"] - last_chord["end"]) < 0.5
            ):  # Allow small gap
                merged_chords[-1]["end"] = chord["end"]
                # Update confidence to average
                merged_chords[-1]["confidence"] = round(
                    (last_chord["confidence"] + chord["confidence"]) / 2, 2
                )
            else:
                merged_chords.append(chord)

        return merged_chords

    return []


def analyze_audio_file(file_path):
    """
    Analyze an audio file and extract musical information including intelligent
    song structure segmentation and chord progressions.

    This function uses Music Information Retrieval (MIR) techniques to:
    - Detect song sections (intro/verse/chorus/bridge/outro)
    - Estimate tempo and key
    - Detect basic chord progressions (major/minor chords)
    - Provide confidence scores for detected sections and chords

    Args:
        file_path (str): Path to the audio file

    Returns:
        dict: Analysis results containing:
            - file_path: Input file path
            - duration: Song duration in seconds
            - tempo: Estimated tempo in BPM
            - key: Estimated musical key
            - key_changes: List of detected key changes with timestamps
            - sections: List of detected sections with:
                - name: Section label (e.g., "Intro", "Verse 1", "Chorus")
                - start: Start time in seconds
                - end: End time in seconds
                - confidence: Confidence score (0-1)
            - beats_detected: Number of beats detected
            - chords: List of detected chords with:
                - name: Chord name (e.g., "C", "Am", "F")
                - start: Start time in seconds
                - end: End time in seconds
                - confidence: Detection confidence (0-1)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    print(f"Loading audio file: {file_path}")

    # Load audio file
    y, sr = librosa.load(file_path)
    duration = librosa.get_duration(y=y, sr=sr)

    print(f"Duration: {duration:.2f} seconds")
    print(f"Sample rate: {sr} Hz")

    # Basic tempo estimation
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

    # Enhanced key estimation using chroma features
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    detected_key, key_changes = detect_key_and_changes(y, sr, chroma)

    # Advanced song structure segmentation using music information retrieval
    sections = analyze_song_structure(y, sr)

    # Chord detection and mapping
    chords = detect_chords(y, sr)

    return {
        "file_path": file_path,
        "duration": round(float(duration), 2),
        "tempo": round(
            float(tempo.item()) if hasattr(tempo, "item") else float(tempo), 1
        ),
        "key": detected_key,
        "key_changes": key_changes,
        "sections": sections,
        "beats_detected": len(beats),
        "chords": chords,
    }


def main():
    """Main function for testing the audio analysis."""
    print("🎵 Sectionist Backend - Audio Analysis Example")
    print("=" * 50)

    # Check for command line argument
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
    else:
        print("Usage: python example.py <audio_file_path>")
        print("\nExample:")
        print("  python example.py /path/to/song.mp3")
        print("\nNote: You can test with any .mp3, .wav, or other audio file")
        return

    try:
        results = analyze_audio_file(audio_file)

        print("\n📊 Analysis Results:")
        print(f"File: {results['file_path']}")
        print(f"Duration: {results['duration']} seconds")
        print(f"Tempo: {results['tempo']} BPM")
        print(f"Key: {results['key']}")
        print(f"Beats detected: {results['beats_detected']}")

        print("\n🎼 Detected Sections:")
        for section in results["sections"]:
            print(f"  {section['name']}: {section['start']}s - {section['end']}s")

        if results["key_changes"]:
            print("\n🔄 Key Changes:")
            for change in results["key_changes"]:
                timestamp = change["timestamp"]
                from_key = change["from_key"]
                to_key = change["to_key"]
                confidence = change["confidence"]
                print(f"  {timestamp}s: {from_key} → {to_key} (conf: {confidence})")
        else:
            print("\n🔄 Key Changes: None detected")

        if results["chords"]:
            print("\n🎸 Chord Progression:")
            for chord in results["chords"]:
                name = chord["name"]
                start = chord["start"]
                end = chord["end"]
                confidence = chord["confidence"]
                print(f"  {name}: {start}s - {end}s (confidence: {confidence})")
        else:
            print("\n🎸 Chord Progression: None detected")

    except Exception as e:
        print(f"❌ Error analyzing audio: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
