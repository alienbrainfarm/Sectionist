#!/usr/bin/env python3
"""
Advanced test script for song structure segmentation.

This creates more realistic test cases that better simulate actual music
complexity to identify specific areas where the current algorithm fails.
"""

import sys
import numpy as np
import soundfile as sf
from example import analyze_audio_file


def create_complex_test_audio():
    """Create more complex synthetic test audio that mimics real song structure."""
    sr = 22050
    # Total 120 seconds (2 minutes)
    
    # More realistic section structure with overlapping frequency content
    sections = [
        # name, start, end, base_freq, harmonics, energy, tempo_factor
        ("intro", 0, 8, 220, [1, 0.3], 0.3, 1.0),        # Intro - soft, simple
        ("verse1", 8, 28, 330, [1, 0.5, 0.2], 0.5, 1.0), # Verse 1 - medium complexity
        ("chorus1", 28, 48, 440, [1, 0.6, 0.4, 0.2], 0.8, 1.1), # Chorus - rich harmonics, louder
        ("verse2", 48, 68, 330, [1, 0.5, 0.2], 0.45, 1.0), # Verse 2 - similar to verse 1
        ("chorus2", 68, 88, 440, [1, 0.6, 0.4, 0.2], 0.8, 1.1), # Chorus - repeat
        ("bridge", 88, 108, 370, [1, 0.3, 0.7], 0.6, 0.9), # Bridge - different harmony, slower
        ("chorus3", 108, 120, 440, [1, 0.6, 0.4, 0.2], 0.85, 1.15), # Final chorus - biggest
    ]
    
    audio = np.array([])
    
    for section_name, start, end, base_freq, harmonics, energy, tempo_factor in sections:
        section_duration = end - start
        t = np.linspace(0, section_duration, int(section_duration * sr))
        
        # Create complex harmonic content
        section_audio = np.zeros_like(t)
        for i, harmonic_amp in enumerate(harmonics):
            freq = base_freq * (i + 1) * tempo_factor
            phase = np.random.random() * 2 * np.pi  # Random phase for complexity
            section_audio += harmonic_amp * np.sin(2 * np.pi * freq * t + phase)
        
        # Apply energy scaling
        section_audio *= energy
        
        # Add realistic effects
        if section_name == "intro":
            # Fade in
            fade_in = np.linspace(0, 1, len(t) // 4)
            section_audio[:len(fade_in)] *= fade_in
        elif section_name == "bridge":
            # Add some modulation for complexity
            modulation = 0.1 * np.sin(2 * np.pi * 0.5 * t)  # 0.5 Hz modulation
            section_audio *= (1 + modulation)
        elif "chorus" in section_name:
            # Add subtle beat pattern
            beat_pattern = 0.1 * np.sin(2 * np.pi * 2 * t)  # 2 Hz beat
            section_audio *= (1 + beat_pattern)
        
        # Add background noise for realism
        noise_level = 0.02 if section_name == "intro" else 0.05
        noise = noise_level * np.random.normal(0, 1, len(section_audio))
        section_audio += noise
        
        # Add smooth transitions between sections
        if len(audio) > 0:
            # Cross-fade between sections (0.5 second overlap)
            crossfade_samples = int(0.5 * sr)
            crossfade_samples = min(crossfade_samples, len(section_audio), len(audio))
            
            if crossfade_samples > 0:
                # Create fade out for previous section end
                fade_out = np.linspace(1, 0, crossfade_samples)
                audio[-crossfade_samples:] *= fade_out
                
                # Create fade in for new section start
                fade_in = np.linspace(0, 1, crossfade_samples)
                section_audio[:crossfade_samples] *= fade_in
                
                # Mix the overlapping parts
                audio[-crossfade_samples:] += section_audio[:crossfade_samples]
                section_audio = section_audio[crossfade_samples:]
        
        audio = np.concatenate([audio, section_audio])
    
    return audio, sr, sections


def create_realistic_song_structure():
    """Create a test case that mimics real pop song structure."""
    sr = 22050
    # Standard pop song structure (3.5 minutes)
    
    sections = [
        # name, start, end, key_freq, chord_progression, energy_profile
        ("intro", 0, 12, 261.63, [261.63, 329.63], [0.2, 0.3]),     # C major intro
        ("verse1", 12, 32, 261.63, [261.63, 349.23, 392.00, 329.63], [0.4, 0.5, 0.4, 0.3]), # C-F-G-E
        ("prechorus", 32, 40, 349.23, [349.23, 392.00], [0.6, 0.7]), # F-G buildup
        ("chorus1", 40, 60, 261.63, [261.63, 392.00, 329.63, 349.23], [0.8, 0.9, 0.8, 0.7]), # C-G-E-F
        ("verse2", 60, 80, 261.63, [261.63, 349.23, 392.00, 329.63], [0.4, 0.5, 0.4, 0.3]), # Same as verse1
        ("prechorus", 80, 88, 349.23, [349.23, 392.00], [0.6, 0.7]), # F-G buildup
        ("chorus2", 88, 108, 261.63, [261.63, 392.00, 329.63, 349.23], [0.8, 0.9, 0.8, 0.7]), # C-G-E-F
        ("bridge", 108, 128, 293.66, [293.66, 369.99, 415.30], [0.5, 0.6, 0.5]), # D-F#-G# (key change)
        ("final_chorus", 128, 158, 261.63, [261.63, 392.00, 329.63, 349.23], [0.9, 1.0, 0.9, 0.8]), # Big finish
        ("outro", 158, 170, 261.63, [261.63], [0.3, 0.1]), # Fade out
    ]
    
    audio = np.array([])
    
    for section_name, start, end, key_freq, chord_prog, energy_prof in sections:
        section_duration = end - start
        chord_duration = section_duration / len(chord_prog)
        
        section_audio = np.array([])
        
        for i, (chord_freq, energy) in enumerate(zip(chord_prog, energy_prof)):
            t = np.linspace(0, chord_duration, int(chord_duration * sr))
            
            # Create chord with multiple harmonics
            chord_audio = np.zeros_like(t)
            # Root, third, fifth
            harmonics = [1.0, 0.6, 0.4]  # Relative amplitudes
            frequencies = [chord_freq, chord_freq * 1.25, chord_freq * 1.5]  # Major chord ratios
            
            for freq, amp in zip(frequencies, harmonics):
                chord_audio += amp * np.sin(2 * np.pi * freq * t)
            
            # Apply energy scaling
            chord_audio *= energy
            
            # Add some subtle rhythm (quarter note pattern)
            if "verse" in section_name or "chorus" in section_name:
                beat_freq = 2.0  # 2 beats per second (120 BPM)
                rhythm = 0.1 * (1 + np.sin(2 * np.pi * beat_freq * t))
                chord_audio *= rhythm
            
            section_audio = np.concatenate([section_audio, chord_audio])
        
        # Section-specific effects
        if section_name == "intro":
            # Gradual fade in
            fade_length = len(section_audio) // 2
            fade_in = np.linspace(0.1, 1, fade_length)
            section_audio[:fade_length] *= fade_in
        elif section_name == "outro":
            # Gradual fade out
            fade_length = len(section_audio) // 2
            fade_out = np.linspace(1, 0.05, fade_length)
            section_audio[-fade_length:] *= fade_out
        elif "prechorus" in section_name:
            # Add intensity buildup
            buildup = np.linspace(1, 1.3, len(section_audio))
            section_audio *= buildup
        elif section_name == "bridge":
            # Add distinctive modulation
            mod_freq = 0.3  # Slow modulation
            modulation = 0.15 * np.sin(2 * np.pi * mod_freq * np.arange(len(section_audio)) / sr)
            section_audio *= (1 + modulation)
        
        # Add realistic noise
        noise = 0.03 * np.random.normal(0, 1, len(section_audio))
        section_audio += noise
        
        audio = np.concatenate([audio, section_audio])
    
    return audio, sr, sections


def evaluate_segmentation_accuracy(detected_sections, expected_sections, tolerance=3.0):
    """
    Evaluate how well the detected sections match expected sections.
    
    Args:
        detected_sections: List of detected sections from algorithm
        expected_sections: List of expected sections  
        tolerance: Time tolerance in seconds for boundary matching
    
    Returns:
        dict: Evaluation metrics
    """
    results = {
        "boundary_accuracy": 0,
        "label_accuracy": 0,
        "timing_errors": [],
        "missed_sections": 0,
        "extra_sections": 0,
        "correctly_labeled": 0
    }
    
    # Check boundary accuracy
    expected_boundaries = []
    for section in expected_sections:
        expected_boundaries.extend([section[1], section[2]])  # start, end times
    expected_boundaries = sorted(set(expected_boundaries))  # Remove duplicates
    
    detected_boundaries = []
    for section in detected_sections:
        detected_boundaries.extend([section["start"], section["end"]])
    detected_boundaries = sorted(set(detected_boundaries))
    
    # Match boundaries within tolerance
    matched_boundaries = 0
    timing_errors = []
    
    for expected_boundary in expected_boundaries:
        best_match = None
        best_error = float('inf')
        
        for detected_boundary in detected_boundaries:
            error = abs(expected_boundary - detected_boundary)
            if error < best_error:
                best_error = error
                best_match = detected_boundary
        
        if best_match is not None and best_error <= tolerance:
            matched_boundaries += 1
            timing_errors.append(best_error)
    
    results["boundary_accuracy"] = matched_boundaries / len(expected_boundaries) if expected_boundaries else 0
    results["timing_errors"] = timing_errors
    results["avg_timing_error"] = np.mean(timing_errors) if timing_errors else 0
    
    # Check section count accuracy
    results["missed_sections"] = max(0, len(expected_sections) - len(detected_sections))
    results["extra_sections"] = max(0, len(detected_sections) - len(expected_sections))
    
    # Check label accuracy (simplified - just check if chorus/verse are correctly identified)
    expected_labels = [section[0].lower() for section in expected_sections]
    detected_labels = [section["name"].lower() for section in detected_sections]
    
    # Count how many expected choruses and verses were detected
    expected_chorus_count = sum(1 for label in expected_labels if "chorus" in label)
    expected_verse_count = sum(1 for label in expected_labels if "verse" in label)
    
    detected_chorus_count = sum(1 for label in detected_labels if "chorus" in label) 
    detected_verse_count = sum(1 for label in detected_labels if "verse" in label)
    
    chorus_accuracy = min(detected_chorus_count, expected_chorus_count) / max(expected_chorus_count, 1)
    verse_accuracy = min(detected_verse_count, expected_verse_count) / max(expected_verse_count, 1)
    
    results["chorus_accuracy"] = chorus_accuracy
    results["verse_accuracy"] = verse_accuracy
    results["label_accuracy"] = (chorus_accuracy + verse_accuracy) / 2
    
    return results


def run_advanced_tests():
    """Run comprehensive tests to identify segmentation weaknesses."""
    print("🧪 Advanced Song Structure Segmentation Tests")
    print("=" * 60)
    
    tests = [
        ("Complex Synthetic Song", create_complex_test_audio),
        ("Realistic Pop Structure", create_realistic_song_structure)
    ]
    
    overall_results = []
    
    for test_name, create_audio_func in tests:
        print(f"\n🎵 Test: {test_name}")
        print("-" * 40)
        
        # Create test audio
        print("Creating test audio...")
        audio, sr, expected_sections = create_audio_func()
        
        # Save test audio
        test_file = f"/tmp/test_{test_name.lower().replace(' ', '_')}.wav"
        sf.write(test_file, audio, sr)
        print(f"✅ Test audio saved: {test_file}")
        
        # Print expected structure
        print("\n📋 Expected Structure:")
        for i, section in enumerate(expected_sections):
            if len(section) >= 3:
                name, start, end = section[0], section[1], section[2] 
                print(f"  {i+1:2d}. {name:12s}: {start:6.1f}s - {end:6.1f}s ({end-start:5.1f}s)")
        
        # Run analysis
        print("\n🔍 Running segmentation analysis...")
        try:
            results = analyze_audio_file(test_file)
            
            print(f"\n📊 Analysis Results:")
            print(f"Duration: {results['duration']}s")
            print(f"Tempo: {results['tempo']} BPM")
            print(f"Key: {results['key']}")
            
            print(f"\n🎼 Detected Sections:")
            detected_sections = results["sections"]
            for i, section in enumerate(detected_sections):
                conf = section["confidence"]
                duration = section["end"] - section["start"] 
                print(f"  {i+1:2d}. {section['name']:12s}: {section['start']:6.1f}s - {section['end']:6.1f}s ({duration:5.1f}s) conf:{conf}")
            
            # Evaluate accuracy
            print(f"\n📈 Accuracy Evaluation:")
            evaluation = evaluate_segmentation_accuracy(detected_sections, expected_sections)
            
            print(f"  Boundary Accuracy: {evaluation['boundary_accuracy']:.1%}")
            print(f"  Average Timing Error: {evaluation['avg_timing_error']:.1f}s")
            print(f"  Label Accuracy: {evaluation['label_accuracy']:.1%}")
            print(f"  Chorus Detection: {evaluation['chorus_accuracy']:.1%}")
            print(f"  Verse Detection: {evaluation['verse_accuracy']:.1%}")
            print(f"  Missed Sections: {evaluation['missed_sections']}")
            print(f"  Extra Sections: {evaluation['extra_sections']}")
            
            overall_results.append({
                "test_name": test_name,
                "evaluation": evaluation,
                "expected_count": len(expected_sections),
                "detected_count": len(detected_sections)
            })
            
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            import traceback
            traceback.print_exc()
    
    # Overall summary
    print(f"\n🎯 Overall Test Summary")
    print("=" * 60)
    
    if overall_results:
        avg_boundary_acc = np.mean([r["evaluation"]["boundary_accuracy"] for r in overall_results])
        avg_timing_error = np.mean([r["evaluation"]["avg_timing_error"] for r in overall_results])
        avg_label_acc = np.mean([r["evaluation"]["label_accuracy"] for r in overall_results])
        
        print(f"Average Boundary Accuracy: {avg_boundary_acc:.1%}")
        print(f"Average Timing Error: {avg_timing_error:.1f}s")  
        print(f"Average Label Accuracy: {avg_label_acc:.1%}")
        
        # Identify key issues
        print(f"\n🔍 Key Issues Identified:")
        if avg_boundary_acc < 0.7:
            print(f"  ⚠️  Poor boundary detection accuracy ({avg_boundary_acc:.1%})")
        if avg_timing_error > 2.0:
            print(f"  ⚠️  High timing errors (avg {avg_timing_error:.1f}s)")
        if avg_label_acc < 0.6:
            print(f"  ⚠️  Poor section labeling accuracy ({avg_label_acc:.1%})")
        
        print(f"\n💡 Recommendations:")
        if avg_boundary_acc < 0.7:
            print(f"  - Implement more sophisticated boundary detection (novelty detection, spectral clustering)")
        if avg_timing_error > 2.0:
            print(f"  - Add beat-synchronous analysis for precise timing")
        if avg_label_acc < 0.6:
            print(f"  - Improve section labeling using musical content analysis")
    
    return overall_results


if __name__ == "__main__":
    results = run_advanced_tests()
    print(f"\n✅ Advanced testing completed!")
    
    # Return exit code based on overall performance
    if results:
        avg_performance = np.mean([r["evaluation"]["boundary_accuracy"] + r["evaluation"]["label_accuracy"] 
                                 for r in results]) / 2
        if avg_performance < 0.5:
            print(f"❌ Overall performance below threshold: {avg_performance:.1%}")
            sys.exit(1)
    
    sys.exit(0)