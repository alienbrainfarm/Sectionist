#!/usr/bin/env python3
"""
Sectionist Backend Example

This script demonstrates basic audio analysis functionality that will be used
by the Sectionist macOS app for song section detection, key detection, and
basic chord mapping.
"""

import os
import sys
import numpy as np

try:
    import librosa
    print("✅ librosa imported successfully")
except ImportError:
    print("❌ librosa not available. Run: pip install -r requirements.txt")
    sys.exit(1)


def analyze_audio_file(file_path):
    """
    Analyze an audio file and extract basic musical information.
    
    Args:
        file_path (str): Path to the audio file
        
    Returns:
        dict: Analysis results containing tempo, key, and basic structure info
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
    key_profiles = np.array([
        [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1],  # C major
        [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0],  # G major
        # Add more key profiles as needed
    ])
    
    # Very basic key detection (just for demonstration)
    chroma_mean = np.mean(chroma, axis=1)
    key_scores = np.dot(key_profiles, chroma_mean)
    detected_key = ["C major", "G major"][np.argmax(key_scores)]
    
    # Basic sectioning (placeholder - would use more sophisticated methods)
    sections = []
    section_length = duration / 4  # Divide into 4 rough sections
    section_names = ["Intro", "Verse", "Chorus", "Outro"]
    
    for i, name in enumerate(section_names):
        start_time = i * section_length
        end_time = min((i + 1) * section_length, duration)
        sections.append({
            "name": name,
            "start": round(start_time, 2),
            "end": round(end_time, 2)
        })
    
    return {
        "file_path": file_path,
        "duration": round(duration, 2),
        "tempo": round(tempo, 1),
        "key": detected_key,
        "sections": sections,
        "beats_detected": len(beats)
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
        
        print(f"\n📊 Analysis Results:")
        print(f"File: {results['file_path']}")
        print(f"Duration: {results['duration']} seconds")
        print(f"Tempo: {results['tempo']} BPM")
        print(f"Key: {results['key']}")
        print(f"Beats detected: {results['beats_detected']}")
        
        print(f"\n🎼 Detected Sections:")
        for section in results['sections']:
            print(f"  {section['name']}: {section['start']}s - {section['end']}s")
            
    except Exception as e:
        print(f"❌ Error analyzing audio: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()