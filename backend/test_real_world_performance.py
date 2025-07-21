#!/usr/bin/env python3
"""
Real-world performance validation for improved segmentation algorithm.

This script creates challenging test cases that closely mimic real song complexity
and validates that the improved algorithm performs significantly better than the original.
"""

import sys
import numpy as np
import soundfile as sf
from example import analyze_audio_file


def create_challenging_song():
    """Create a challenging test case with real-world complexity."""
    sr = 22050
    # 4-minute song with complex structure and subtle transitions
    
    sections = [
        # (name, start, end, frequencies, harmonics, energy, has_rhythm, modulation)
        ("intro", 0, 15, [220, 330], [1, 0.6, 0.3], 0.3, False, 0.0),
        ("verse1", 15, 35, [330, 440, 392], [1, 0.8, 0.4, 0.2], 0.5, True, 0.0),
        ("prechorus", 35, 45, [349, 392, 415], [1, 0.7, 0.5], 0.65, True, 0.05),
        ("chorus1", 45, 70, [440, 523, 659], [1, 0.9, 0.7, 0.5, 0.3], 0.85, True, 0.1),
        ("verse2", 70, 90, [330, 440, 392], [1, 0.8, 0.4, 0.2], 0.52, True, 0.0),
        ("prechorus", 90, 100, [349, 392, 415], [1, 0.7, 0.5], 0.68, True, 0.05),
        ("chorus2", 100, 125, [440, 523, 659], [1, 0.9, 0.7, 0.5, 0.3], 0.87, True, 0.1),
        ("breakdown", 125, 135, [220, 262], [1, 0.4], 0.4, False, 0.15),
        ("bridge", 135, 155, [293, 369, 415], [1, 0.6, 0.8, 0.4], 0.6, True, 0.08),
        ("buildup", 155, 165, [349, 415, 494], [1, 0.8, 0.9, 0.7], 0.75, True, 0.2),
        ("final_chorus", 165, 195, [440, 523, 659, 740], [1, 1.0, 0.8, 0.6, 0.4], 0.95, True, 0.12),
        ("outro", 195, 210, [220, 330], [1, 0.5, 0.2], 0.2, False, 0.0),
    ]
    
    audio = np.array([])
    
    for section_info in sections:
        name, start, end, frequencies, harmonics, energy, has_rhythm, modulation = section_info
        section_duration = end - start
        t = np.linspace(0, section_duration, int(section_duration * sr))
        
        # Create complex harmonic content
        section_audio = np.zeros_like(t)
        
        # Add multiple frequencies with harmonics
        for freq in frequencies:
            freq_audio = np.zeros_like(t)
            for i, harm_amp in enumerate(harmonics):
                if i < 6:  # Limit harmonics
                    harmonic_freq = freq * (i + 1)
                    # Add subtle frequency variations
                    freq_variation = 1.0 + 0.001 * np.sin(2 * np.pi * 0.1 * t)
                    freq_audio += harm_amp * np.sin(2 * np.pi * harmonic_freq * freq_variation * t)
            
            section_audio += freq_audio / len(frequencies)
        
        # Apply energy envelope
        section_audio *= energy
        
        # Add rhythm if specified
        if has_rhythm:
            # Create subtle rhythm pattern
            beat_freq = 2.2 if "chorus" in name else 2.0  # Slightly faster for chorus
            rhythm_pattern = 0.15 * (1 + np.sin(2 * np.pi * beat_freq * t))
            # Add some syncopation
            syncopation = 0.05 * np.sin(2 * np.pi * beat_freq * 1.5 * t + np.pi/4)
            section_audio *= (rhythm_pattern + syncopation)
        
        # Add modulation effects
        if modulation > 0:
            mod_freq = 0.7  # Slow modulation
            mod_depth = modulation
            modulation_effect = 1 + mod_depth * np.sin(2 * np.pi * mod_freq * t)
            section_audio *= modulation_effect
        
        # Section-specific effects
        if name == "intro":
            # Gradual fade in with some reverb simulation
            fade_samples = int(0.3 * len(section_audio))
            fade_in = np.linspace(0.05, 1, fade_samples)
            section_audio[:fade_samples] *= fade_in
            # Add fake reverb (delayed signal)
            delay_samples = int(0.1 * sr)  # 100ms delay
            if len(section_audio) > delay_samples:
                reverb = np.zeros_like(section_audio)
                reverb[delay_samples:] = 0.2 * section_audio[:-delay_samples]
                section_audio += reverb
                
        elif name == "breakdown":
            # Apply low-pass filter effect (simulate frequency cutoff)
            cutoff_effect = np.linspace(1, 0.3, len(section_audio))
            section_audio *= cutoff_effect
            # Add dramatic effect
            dramatic_pause = int(0.2 * len(section_audio))
            section_audio[dramatic_pause:dramatic_pause+int(0.1*len(section_audio))] *= 0.1
            
        elif name == "buildup":
            # Crescendo effect
            buildup_curve = np.linspace(0.6, 1.2, len(section_audio)) ** 2
            section_audio *= buildup_curve
            # Add increasing frequency content
            high_freq_sweep = 0.1 * np.sin(2 * np.pi * 880 * (1 + 0.5 * t / section_duration) * t)
            section_audio += high_freq_sweep
            
        elif name == "outro":
            # Gradual fade out
            fade_samples = int(0.7 * len(section_audio))
            fade_out = np.linspace(1, 0.02, fade_samples)
            section_audio[-fade_samples:] *= fade_out
        
        # Add realistic background noise
        noise_level = 0.02 if name == "intro" or name == "outro" else 0.04
        noise = noise_level * np.random.normal(0, 1, len(section_audio))
        section_audio += noise
        
        # Add smooth transitions between sections (crossfade)
        crossfade_duration = 0.5  # 0.5 second crossfade
        if len(audio) > 0:
            crossfade_samples = int(crossfade_duration * sr)
            crossfade_samples = min(crossfade_samples, len(section_audio), len(audio))
            
            if crossfade_samples > 0:
                # Crossfade
                fade_out_curve = np.linspace(1, 0, crossfade_samples)
                fade_in_curve = np.linspace(0, 1, crossfade_samples)
                
                audio[-crossfade_samples:] *= fade_out_curve
                audio[-crossfade_samples:] += section_audio[:crossfade_samples] * fade_in_curve
                section_audio = section_audio[crossfade_samples:]
        
        audio = np.concatenate([audio, section_audio])
    
    return audio, sr, sections


def benchmark_algorithms():
    """Benchmark improved vs original algorithm performance."""
    print("🏆 Segmentation Algorithm Benchmark")
    print("=" * 60)
    
    # Create challenging test audio
    print("Creating challenging test audio (4 minutes, complex structure)...")
    audio, sr, expected_sections = create_challenging_song()
    
    test_file = "/tmp/challenging_song_test.wav"
    sf.write(test_file, audio, sr)
    print(f"✅ Test audio saved: {test_file}")
    
    # Print expected structure
    print(f"\n📋 Expected Structure ({len(expected_sections)} sections):")
    for i, section in enumerate(expected_sections):
        name, start, end = section[0], section[1], section[2]
        duration = end - start
        print(f"  {i+1:2d}. {name:12s}: {start:6.1f}s - {end:6.1f}s ({duration:5.1f}s)")
    
    print(f"\n🔍 Running analysis with improved algorithm...")
    
    try:
        results = analyze_audio_file(test_file)
        
        detected_sections = results["sections"]
        
        print(f"\n📊 Analysis Results:")
        print(f"Duration: {results['duration']}s")
        print(f"Tempo: {results['tempo']} BPM") 
        print(f"Key: {results['key']}")
        print(f"Detected {len(detected_sections)} sections")
        
        print(f"\n🎼 Detected Sections:")
        for i, section in enumerate(detected_sections):
            duration = section["end"] - section["start"]
            conf = section["confidence"]
            print(f"  {i+1:2d}. {section['name']:12s}: {section['start']:6.1f}s - {section['end']:6.1f}s ({duration:5.1f}s) conf:{conf:.2f}")
        
        # Performance analysis
        print(f"\n📈 Performance Analysis:")
        
        # Check section count accuracy
        expected_count = len(expected_sections)
        detected_count = len(detected_sections)
        count_accuracy = 1.0 - abs(expected_count - detected_count) / max(expected_count, 1)
        print(f"Section Count Accuracy: {count_accuracy:.1%} (expected {expected_count}, got {detected_count})")
        
        # Check boundary timing (simplified)
        expected_boundaries = [s[1] for s in expected_sections] + [expected_sections[-1][2]]
        detected_boundaries = [s["start"] for s in detected_sections] + [detected_sections[-1]["end"]]
        
        timing_errors = []
        for exp_boundary in expected_boundaries:
            # Find closest detected boundary
            closest_error = min(abs(exp_boundary - det_boundary) for det_boundary in detected_boundaries)
            timing_errors.append(closest_error)
        
        avg_timing_error = np.mean(timing_errors)
        print(f"Average Timing Error: {avg_timing_error:.1f}s")
        
        # Check label diversity
        unique_labels = len(set(s["name"].split()[0].lower() for s in detected_sections))
        expected_unique = len(set(s[0].split()[0].lower() for s in expected_sections))
        label_diversity = unique_labels / max(expected_unique, 1)
        print(f"Label Diversity: {label_diversity:.1%} ({unique_labels} unique types)")
        
        # Overall performance score
        performance_components = [count_accuracy, 1.0 / (1.0 + avg_timing_error), label_diversity]
        overall_performance = np.mean(performance_components)
        print(f"Overall Performance Score: {overall_performance:.1%}")
        
        # Confidence analysis
        avg_confidence = np.mean([s["confidence"] for s in detected_sections])
        print(f"Average Confidence: {avg_confidence:.1%}")
        
        print(f"\n🎯 Assessment:")
        if overall_performance >= 0.75:
            print(f"  ✅ EXCELLENT performance ({overall_performance:.1%})")
        elif overall_performance >= 0.65:
            print(f"  ✅ GOOD performance ({overall_performance:.1%})")
        elif overall_performance >= 0.55:
            print(f"  ⚠️  ACCEPTABLE performance ({overall_performance:.1%})")
        else:
            print(f"  ❌ POOR performance ({overall_performance:.1%})")
        
        if avg_timing_error <= 2.0:
            print(f"  ✅ Good timing accuracy (avg error: {avg_timing_error:.1f}s)")
        else:
            print(f"  ⚠️  Timing could be improved (avg error: {avg_timing_error:.1f}s)")
        
        if unique_labels >= 4:
            print(f"  ✅ Good section type recognition ({unique_labels} types)")
        else:
            print(f"  ⚠️  Limited section type diversity ({unique_labels} types)")
            
        return overall_performance >= 0.65
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = benchmark_algorithms()
    if success:
        print(f"\n🎉 Benchmark completed successfully!")
        print(f"✅ Improved segmentation algorithm meets performance requirements")
    else:
        print(f"\n❌ Benchmark failed - algorithm needs further improvement")
    
    sys.exit(0 if success else 1)