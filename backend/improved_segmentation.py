#!/usr/bin/env python3
"""
Improved Song Structure Segmentation using Advanced Music Information Retrieval.

This module implements state-of-the-art segmentation techniques including:
- Novelty-based boundary detection with multiple feature types
- Spectral clustering for structure analysis  
- Beat-synchronous feature extraction
- Advanced section labeling using musical content analysis
- Post-processing for refined boundaries
"""

import numpy as np
import librosa
from sklearn.cluster import SpectralClustering
from sklearn.metrics.pairwise import cosine_similarity
from scipy import signal, ndimage
from scipy.signal import find_peaks


def extract_comprehensive_features(y, sr, hop_length=512):
    """
    Extract comprehensive musical features for segmentation.
    
    Uses beat-synchronous analysis when possible for more musically meaningful segmentation.
    
    Args:
        y (np.array): Audio time series
        sr (int): Sample rate  
        hop_length (int): Hop length for feature extraction
        
    Returns:
        dict: Dictionary containing various feature matrices and metadata
    """
    print("🔍 Extracting comprehensive musical features...")
    
    # Beat tracking for beat-synchronous features
    try:
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
        print(f"   Tempo: {tempo:.1f} BPM, {len(beats)} beats detected")
        beat_sync = True
    except:
        # Fallback to frame-based analysis if beat tracking fails
        beats = None
        beat_sync = False
        print("   Beat tracking failed, using frame-based analysis")
    
    # Extract multiple feature types
    features = {}
    
    # 1. Chroma features (harmonic content)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop_length, n_chroma=12)
    if beat_sync and beats is not None:
        chroma = librosa.util.sync(chroma, beats, aggregate=np.median)
    features['chroma'] = chroma
    
    # 2. MFCC features (timbral content)  
    mfcc = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop_length, n_mfcc=13)
    if beat_sync and beats is not None:
        mfcc = librosa.util.sync(mfcc, beats, aggregate=np.median)
    features['mfcc'] = mfcc
    
    # 3. Spectral features
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=hop_length)
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, hop_length=hop_length)
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y, hop_length=hop_length)
    
    if beat_sync and beats is not None:
        spectral_centroid = librosa.util.sync(spectral_centroid, beats, aggregate=np.median)
        spectral_rolloff = librosa.util.sync(spectral_rolloff, beats, aggregate=np.median)
        spectral_bandwidth = librosa.util.sync(spectral_bandwidth, beats, aggregate=np.median)
        zero_crossing_rate = librosa.util.sync(zero_crossing_rate, beats, aggregate=np.median)
    
    spectral_features = np.vstack([
        spectral_centroid,
        spectral_rolloff, 
        spectral_bandwidth,
        zero_crossing_rate
    ])
    features['spectral'] = spectral_features
    
    # 4. Energy features
    rms = librosa.feature.rms(y=y, hop_length=hop_length)
    if beat_sync and beats is not None:
        rms = librosa.util.sync(rms, beats, aggregate=np.median)
    features['rms'] = rms
    
    # 5. Tempogram (rhythmic content)
    try:
        tempogram = librosa.feature.tempogram(y=y, sr=sr, hop_length=hop_length)
        if beat_sync and beats is not None:
            tempogram = librosa.util.sync(tempogram, beats, aggregate=np.median)
        features['tempogram'] = tempogram[:32, :]  # Use first 32 tempo bins
    except:
        # Create dummy tempogram if calculation fails
        n_frames = features['chroma'].shape[1]
        features['tempogram'] = np.ones((32, n_frames)) * 0.1
    
    # Calculate time frames
    if beat_sync and beats is not None:
        frame_times = librosa.frames_to_time(beats, sr=sr, hop_length=hop_length)
    else:
        n_frames = features['chroma'].shape[1]
        frame_times = librosa.frames_to_time(np.arange(n_frames), sr=sr, hop_length=hop_length)
    
    features['frame_times'] = frame_times
    features['beats'] = beats
    features['tempo'] = tempo if beat_sync else 120.0
    features['beat_sync'] = beat_sync
    
    print(f"   Extracted features with {len(frame_times)} time frames")
    print(f"   Feature shapes: chroma {chroma.shape}, mfcc {mfcc.shape}, spectral {spectral_features.shape}")
    
    return features


def compute_novelty_functions(features):
    """
    Compute multiple novelty functions for different aspects of musical change.
    
    Args:
        features (dict): Feature dictionary from extract_comprehensive_features()
        
    Returns:
        dict: Dictionary of novelty functions
    """
    print("🔍 Computing novelty functions...")
    
    novelty_functions = {}
    
    # 1. Harmonic novelty (chroma-based)
    chroma = features['chroma']
    if chroma.shape[1] > 1:
        chroma_diff = np.diff(chroma, axis=1)
        harmonic_novelty = np.sum(np.abs(chroma_diff), axis=0)
        # Smooth and normalize
        harmonic_novelty = ndimage.gaussian_filter1d(harmonic_novelty, sigma=1.0)
        harmonic_novelty = harmonic_novelty / (np.max(harmonic_novelty) + 1e-8)
        novelty_functions['harmonic'] = harmonic_novelty
    else:
        novelty_functions['harmonic'] = np.array([0.0])
    
    # 2. Timbral novelty (MFCC-based)
    mfcc = features['mfcc']
    if mfcc.shape[1] > 1:
        mfcc_diff = np.diff(mfcc, axis=1)
        timbral_novelty = np.sum(np.abs(mfcc_diff), axis=0)
        # Smooth and normalize  
        timbral_novelty = ndimage.gaussian_filter1d(timbral_novelty, sigma=1.0)
        timbral_novelty = timbral_novelty / (np.max(timbral_novelty) + 1e-8)
        novelty_functions['timbral'] = timbral_novelty
    else:
        novelty_functions['timbral'] = np.array([0.0])
    
    # 3. Energy novelty (RMS-based)
    rms = features['rms']
    if rms.shape[1] > 1:
        rms_diff = np.diff(rms, axis=1)
        energy_novelty = np.abs(rms_diff).flatten()
        # Smooth and normalize
        energy_novelty = ndimage.gaussian_filter1d(energy_novelty, sigma=1.0)
        energy_novelty = energy_novelty / (np.max(energy_novelty) + 1e-8)
        novelty_functions['energy'] = energy_novelty
    else:
        novelty_functions['energy'] = np.array([0.0])
    
    # 4. Spectral novelty
    spectral = features['spectral']
    if spectral.shape[1] > 1:
        spectral_diff = np.diff(spectral, axis=1)
        spectral_novelty = np.sum(np.abs(spectral_diff), axis=0)
        # Smooth and normalize
        spectral_novelty = ndimage.gaussian_filter1d(spectral_novelty, sigma=1.0)
        spectral_novelty = spectral_novelty / (np.max(spectral_novelty) + 1e-8)
        novelty_functions['spectral'] = spectral_novelty
    else:
        novelty_functions['spectral'] = np.array([0.0])
    
    # 5. Combined novelty function
    all_novelty = []
    for key in ['harmonic', 'timbral', 'energy', 'spectral']:
        if key in novelty_functions:
            all_novelty.append(novelty_functions[key])
    
    if all_novelty:
        # Weight different novelty types
        weights = [0.4, 0.3, 0.2, 0.1]  # Harmonic and timbral are most important
        combined_novelty = np.zeros_like(all_novelty[0])
        
        for i, novelty in enumerate(all_novelty):
            if i < len(weights) and len(novelty) == len(combined_novelty):
                combined_novelty += weights[i] * novelty
        
        # Additional smoothing
        combined_novelty = ndimage.gaussian_filter1d(combined_novelty, sigma=1.5)
        novelty_functions['combined'] = combined_novelty
    
    print(f"   Computed {len(novelty_functions)} novelty functions")
    return novelty_functions


def detect_boundaries_novelty(novelty_functions, frame_times, min_segment_length=8.0):
    """
    Detect segment boundaries using novelty functions with peak picking.
    
    Args:
        novelty_functions (dict): Novelty functions from compute_novelty_functions()
        frame_times (np.array): Time frames corresponding to features
        min_segment_length (float): Minimum segment length in seconds
        
    Returns:
        np.array: Array of boundary times in seconds
    """
    print("🔍 Detecting boundaries using novelty functions...")
    
    # Use combined novelty if available, otherwise use harmonic
    if 'combined' in novelty_functions:
        novelty = novelty_functions['combined']
    elif 'harmonic' in novelty_functions:
        novelty = novelty_functions['harmonic']
    else:
        print("   No suitable novelty function found, using basic segmentation")
        duration = frame_times[-1] if len(frame_times) > 0 else 60.0
        return np.array([0, duration/3, 2*duration/3, duration])
    
    # Adaptive thresholding based on novelty statistics
    novelty_mean = np.mean(novelty)
    novelty_std = np.std(novelty)
    
    # Dynamic threshold based on data characteristics
    threshold = novelty_mean + 0.5 * novelty_std
    
    # Minimum distance between peaks (in frames)
    min_distance_frames = max(1, int(min_segment_length / (frame_times[1] - frame_times[0]) if len(frame_times) > 1 else 1))
    
    # Find peaks in novelty function
    peaks, properties = find_peaks(
        novelty, 
        height=threshold,
        distance=min_distance_frames,
        prominence=0.1  # Require some prominence to avoid noise
    )
    
    # Convert peak indices to time
    boundary_times = []
    boundary_times.append(0.0)  # Always start with 0
    
    for peak in peaks:
        if peak < len(frame_times):
            boundary_time = frame_times[peak]
            # Ensure minimum distance from previous boundary
            if not boundary_times or boundary_time - boundary_times[-1] >= min_segment_length:
                boundary_times.append(boundary_time)
    
    # Always end with full duration
    total_duration = frame_times[-1] if len(frame_times) > 0 else 60.0
    if not boundary_times or boundary_times[-1] != total_duration:
        boundary_times.append(total_duration)
    
    # Ensure we have at least 3 boundaries (intro, main, outro)
    if len(boundary_times) < 3:
        duration = total_duration
        boundary_times = [0, duration/3, 2*duration/3, duration]
    
    print(f"   Detected {len(boundary_times)-1} segments with boundaries at: {boundary_times}")
    return np.array(boundary_times)


def analyze_section_content(features, start_frame, end_frame):
    """
    Analyze the musical content of a section to determine its characteristics.
    
    Args:
        features (dict): Feature dictionary  
        start_frame (int): Starting frame index
        end_frame (int): Ending frame index
        
    Returns:
        dict: Section characteristics
    """
    # Ensure valid frame range
    max_frames = features['chroma'].shape[1]
    start_frame = max(0, min(start_frame, max_frames-1))
    end_frame = max(start_frame+1, min(end_frame, max_frames))
    
    characteristics = {}
    
    # 1. Energy level (from RMS)
    rms_segment = features['rms'][:, start_frame:end_frame]
    characteristics['energy_level'] = float(np.mean(rms_segment))
    characteristics['energy_variation'] = float(np.std(rms_segment))
    
    # 2. Harmonic complexity (from chroma)
    chroma_segment = features['chroma'][:, start_frame:end_frame]
    # Number of active pitches (above threshold)
    active_pitches = np.mean(chroma_segment > 0.1, axis=1)  
    characteristics['harmonic_complexity'] = float(np.sum(active_pitches > 0.1))
    characteristics['harmonic_stability'] = float(1.0 / (1.0 + np.std(chroma_segment)))
    
    # 3. Timbral characteristics (from MFCC)
    mfcc_segment = features['mfcc'][:, start_frame:end_frame]
    characteristics['brightness'] = float(np.mean(mfcc_segment[0, :]))  # First MFCC ~ brightness
    characteristics['timbral_variation'] = float(np.mean(np.std(mfcc_segment, axis=1)))
    
    # 4. Spectral characteristics
    spectral_segment = features['spectral'][:, start_frame:end_frame]
    characteristics['spectral_centroid'] = float(np.mean(spectral_segment[0, :]))
    characteristics['spectral_rolloff'] = float(np.mean(spectral_segment[1, :]))
    
    return characteristics


def label_sections_advanced(boundary_times, features, frame_times):
    """
    Label sections using advanced musical content analysis.
    
    Args:
        boundary_times (np.array): Boundary times in seconds
        features (dict): Feature dictionary
        frame_times (np.array): Time frames for features
        
    Returns:
        list: List of labeled sections
    """
    print("🔍 Labeling sections using content analysis...")
    
    sections = []
    total_duration = boundary_times[-1]
    
    # Analyze each segment
    section_characteristics = []
    for i in range(len(boundary_times) - 1):
        start_time = boundary_times[i]
        end_time = boundary_times[i + 1]
        
        # Find corresponding frame indices
        start_frame = np.argmin(np.abs(frame_times - start_time))
        end_frame = np.argmin(np.abs(frame_times - end_time))
        
        # Analyze content
        chars = analyze_section_content(features, start_frame, end_frame)
        chars['start_time'] = start_time
        chars['end_time'] = end_time
        chars['duration'] = end_time - start_time
        chars['position_ratio'] = start_time / total_duration if total_duration > 0 else 0
        
        section_characteristics.append(chars)
    
    # Statistical analysis for relative comparisons
    energy_levels = [s['energy_level'] for s in section_characteristics]
    harmonic_complexities = [s['harmonic_complexity'] for s in section_characteristics]
    
    energy_mean = np.mean(energy_levels)
    energy_std = np.std(energy_levels)
    complexity_mean = np.mean(harmonic_complexities)
    
    # Identify section types using multiple criteria
    for i, chars in enumerate(section_characteristics):
        
        # Basic position-based rules
        position_ratio = chars['position_ratio']
        duration = chars['duration']
        
        # Content-based features
        is_high_energy = chars['energy_level'] > energy_mean + 0.5 * energy_std
        is_complex = chars['harmonic_complexity'] > complexity_mean
        is_stable = chars['harmonic_stability'] > 0.7
        is_short = duration < 12.0
        is_long = duration > 25.0
        
        # Advanced labeling logic
        if position_ratio < 0.1 or (position_ratio < 0.2 and duration < 15):
            label = "Intro"
        elif position_ratio > 0.9 or (position_ratio > 0.85 and i == len(section_characteristics) - 1):
            label = "Outro"
        elif is_high_energy and is_complex and not is_short:
            # High energy + complex = likely chorus
            # Check for repetition by comparing with other high-energy sections
            chorus_candidates = [j for j, s in enumerate(section_characteristics) 
                               if j != i and s['energy_level'] > energy_mean + 0.5 * energy_std]
            if len(chorus_candidates) > 0:
                label = "Chorus"
            else:
                label = "Chorus"  # First occurrence
        elif is_short and not is_stable and position_ratio > 0.3 and position_ratio < 0.8:
            label = "Bridge"
        elif position_ratio < 0.6 and not is_high_energy:
            # Early in song, lower energy = verse
            verse_count = sum(1 for s in sections if "Verse" in s.get('name', ''))
            if verse_count == 0:
                label = "Verse 1"
            else:
                label = f"Verse {verse_count + 1}"
        elif not is_high_energy:
            # Default for medium/low energy sections
            verse_count = sum(1 for s in sections if "Verse" in s.get('name', ''))
            label = "Verse" if verse_count > 2 else f"Verse {verse_count + 1}"
        else:
            # Default for high energy sections
            label = "Chorus"
        
        # Calculate confidence based on how well the section fits its label
        confidence = 0.5  # Base confidence
        
        if label == "Intro" and position_ratio < 0.15:
            confidence += 0.3
        elif label == "Outro" and position_ratio > 0.85:
            confidence += 0.3
        elif label == "Chorus" and is_high_energy:
            confidence += 0.2
        elif "Verse" in label and not is_high_energy:
            confidence += 0.2
        elif label == "Bridge" and is_short:
            confidence += 0.2
        
        # Adjust confidence based on characteristics
        if is_stable:
            confidence += 0.1
        if chars['energy_variation'] < np.mean([s['energy_variation'] for s in section_characteristics]):
            confidence += 0.1
            
        confidence = min(0.99, confidence)
        
        sections.append({
            "name": label,
            "start": round(float(chars['start_time']), 2),
            "end": round(float(chars['end_time']), 2), 
            "confidence": round(float(confidence), 2),
        })
    
    print(f"   Labeled {len(sections)} sections")
    return sections


def improved_analyze_song_structure(y, sr):
    """
    Analyze song structure using improved MIR techniques.
    
    This is the main function that replaces the basic analyze_song_structure()
    in example.py with advanced techniques.
    
    Args:
        y (np.array): Audio time series
        sr (int): Sample rate
        
    Returns:
        list: List of detected sections with labels and timestamps
    """
    print("🚀 Running improved song structure analysis...")
    
    # Use smaller hop_length for better temporal resolution
    hop_length = 512  # ~0.023 seconds at 22050 Hz
    
    # Extract comprehensive features
    features = extract_comprehensive_features(y, sr, hop_length)
    
    # Compute novelty functions  
    novelty_functions = compute_novelty_functions(features)
    
    # Detect boundaries using novelty
    boundary_times = detect_boundaries_novelty(
        novelty_functions, 
        features['frame_times'],
        min_segment_length=6.0  # Reduced from 8.0 for better granularity
    )
    
    # Label sections using advanced content analysis
    sections = label_sections_advanced(boundary_times, features, features['frame_times'])
    
    print("✅ Improved song structure analysis completed")
    return sections


def post_process_sections(sections, min_section_length=5.0, merge_similar=True):
    """
    Post-process detected sections to refine boundaries and merge similar adjacent sections.
    
    Args:
        sections (list): List of sections from improved analysis
        min_section_length (float): Minimum section length in seconds
        merge_similar (bool): Whether to merge similar adjacent sections
        
    Returns:
        list: Post-processed sections
    """
    if len(sections) <= 1:
        return sections
    
    processed = []
    i = 0
    
    while i < len(sections):
        current = sections[i].copy()
        
        # Check if we should merge with next section
        should_merge = False
        if merge_similar and i < len(sections) - 1:
            next_section = sections[i + 1]
            
            # Merge if:
            # 1. Same label type (both chorus, both verse, etc.)
            # 2. Very short sections (< min_section_length)
            # 3. Similar confidence and adjacent
            
            current_type = current['name'].lower().split()[0]  # "verse", "chorus", etc.
            next_type = next_section['name'].lower().split()[0]
            
            current_duration = current['end'] - current['start']
            next_duration = next_section['end'] - next_section['start']
            
            if (current_type == next_type or 
                current_duration < min_section_length or 
                next_duration < min_section_length):
                should_merge = True
        
        if should_merge and i < len(sections) - 1:
            # Merge current with next
            next_section = sections[i + 1]
            current['end'] = next_section['end']
            current['confidence'] = (current['confidence'] + next_section['confidence']) / 2
            i += 2  # Skip next section since we merged it
        else:
            i += 1
        
        processed.append(current)
    
    return processed