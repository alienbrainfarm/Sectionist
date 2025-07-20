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


def analyze_audio_file(file_path):
    """
    Analyze an audio file and extract musical information including intelligent
    song structure segmentation.

    This function uses Music Information Retrieval (MIR) techniques to:
    - Detect song sections (intro/verse/chorus/bridge/outro)
    - Estimate tempo and key
    - Provide confidence scores for detected sections

    Args:
        file_path (str): Path to the audio file

    Returns:
        dict: Analysis results containing:
            - file_path: Input file path
            - duration: Song duration in seconds
            - tempo: Estimated tempo in BPM
            - key: Estimated musical key
            - sections: List of detected sections with:
                - name: Section label (e.g., "Intro", "Verse 1", "Chorus")
                - start: Start time in seconds
                - end: End time in seconds
                - confidence: Confidence score (0-1)
            - beats_detected: Number of beats detected
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

    # Simple key estimation using chroma features
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    key_profiles = np.array(
        [
            [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1],  # C major
            [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0],  # G major
            # Add more key profiles as needed
        ]
    )

    # Very basic key detection (just for demonstration)
    chroma_mean = np.mean(chroma, axis=1)
    key_scores = np.dot(key_profiles, chroma_mean)
    detected_key = ["C major", "G major"][np.argmax(key_scores)]

    # Advanced song structure segmentation using music information retrieval
    sections = analyze_song_structure(y, sr)

    return {
        "file_path": file_path,
        "duration": round(float(duration), 2),
        "tempo": round(
            float(tempo.item()) if hasattr(tempo, "item") else float(tempo), 1
        ),
        "key": detected_key,
        "sections": sections,
        "beats_detected": len(beats),
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

    except Exception as e:
        print(f"❌ Error analyzing audio: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
