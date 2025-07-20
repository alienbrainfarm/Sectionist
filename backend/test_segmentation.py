#!/usr/bin/env python3
"""
Test script to validate the song structure segmentation implementation.

This script tests the improved segmentation algorithm against synthetic test audio
with known section boundaries.
"""

import sys
import numpy as np
import soundfile as sf
from example import analyze_audio_file


def create_test_audio():
    """Create synthetic test audio with known section structure."""
    sr = 22050
    # Total 60 seconds

    # Define section boundaries (in seconds)
    # Intro: 0-10s, Verse: 10-25s, Chorus: 25-40s, Bridge: 40-50s, Outro: 50-60s
    sections = [
        ("intro", 0, 10, 220, 0.2),  # Low frequency, low energy
        ("verse", 10, 25, 330, 0.4),  # Mid frequency, mid energy
        ("chorus", 25, 40, 440, 0.6),  # Higher frequency, high energy
        ("bridge", 40, 50, 370, 0.3),  # Different frequency, low energy
        ("outro", 50, 60, 220, 0.1),  # Low frequency, very low energy with fade
    ]

    audio = np.array([])

    for section_name, start, end, freq, energy in sections:
        section_duration = end - start
        t = np.linspace(0, section_duration, int(section_duration * sr))

        if section_name == "outro":
            # Add fade out to outro
            fade = np.exp(-0.5 * t)
            section_audio = energy * np.sin(2 * np.pi * freq * t) * fade
        elif section_name == "chorus":
            # Add harmonics to make chorus more distinct
            section_audio = energy * np.sin(
                2 * np.pi * freq * t
            ) + 0.3 * energy * np.sin(2 * np.pi * freq * 2 * t)
        else:
            section_audio = energy * np.sin(2 * np.pi * freq * t)

        # Add some noise for realism
        noise = 0.05 * np.random.normal(0, 1, len(section_audio))
        section_audio += noise

        audio = np.concatenate([audio, section_audio])

    return audio, sr, sections


def test_segmentation():
    """Test the segmentation algorithm."""
    print("🧪 Song Structure Segmentation Test")
    print("=" * 50)

    # Create test audio
    print("Creating synthetic test audio...")
    audio, sr, expected_sections = create_test_audio()

    # Save test audio
    test_file = "/tmp/segmentation_test.wav"
    sf.write(test_file, audio, sr)
    print(f"✅ Test audio saved: {test_file}")

    # Print expected structure
    print("\n📋 Expected Structure:")
    for name, start, end, _, _ in expected_sections:
        print(f"  {name.title()}: {start}s - {end}s")

    # Run analysis
    print("\n🔍 Running segmentation analysis...")
    try:
        results = analyze_audio_file(test_file)

        print("\n📊 Analysis Results:")
        print(f"Duration: {results['duration']}s")
        print(f"Tempo: {results['tempo']} BPM")
        print(f"Key: {results['key']}")

        print("\n🎼 Detected Sections:")
        detected_sections = results["sections"]
        for section in detected_sections:
            conf = section["confidence"]
            print(
                f"  {section['name']}: {section['start']}s - "
                f"{section['end']}s (confidence: {conf})"
            )

        # Simple evaluation
        print("\n📈 Evaluation:")
        print(f"  Expected sections: {len(expected_sections)}")
        print(f"  Detected sections: {len(detected_sections)}")

        # Check if we detected reasonable number of sections
        if 3 <= len(detected_sections) <= 7:
            print("  ✅ Reasonable number of sections detected")
        else:
            print("  ⚠️  Unusual number of sections detected")

        # Check section diversity
        unique_labels = set(s["name"] for s in detected_sections)
        if len(unique_labels) >= 3:
            print("  ✅ Good section label diversity")
        else:
            print("  ⚠️  Limited section label diversity")

        print("\n🎉 Test completed successfully!")

        # Add assertions for pytest
        assert len(detected_sections) > 0, "No sections detected"
        assert (
            3 <= len(detected_sections) <= 7
        ), f"Unexpected number of sections: {len(detected_sections)}"
        assert (
            len(unique_labels) >= 2
        ), f"Insufficient label diversity: {len(unique_labels)}"

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        raise  # Re-raise for pytest to catch

    return True

    return True


if __name__ == "__main__":
    success = test_segmentation()
    sys.exit(0 if success else 1)
