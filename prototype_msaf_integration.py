#!/usr/bin/env python3
"""
Quick prototype to demonstrate MSAF integration potential.
This script shows how easy it would be to integrate MSAF into the existing backend.
"""

import sys
import os
import time
import traceback

# Add the parent directory to the path so we can import from the backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from example import analyze_audio_file
    SECTIONIST_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Could not import Sectionist backend: {e}")
    SECTIONIST_AVAILABLE = False

def test_msaf_availability():
    """Test if MSAF can be installed and used"""
    try:
        import msaf
        print(f"✅ MSAF available: version {msaf.__version__ if hasattr(msaf, '__version__') else 'unknown'}")
        return True
    except ImportError:
        print("❌ MSAF not available. Install with: pip install msaf")
        return False

def create_test_audio():
    """Create a simple synthetic test audio file"""
    try:
        import numpy as np
        import soundfile as sf
        
        # Create simple test audio (sine waves with different frequencies for different sections)
        sr = 22050
        duration = 60  # 1 minute test
        
        # Section 1: Low frequency (intro)
        t1 = np.linspace(0, 15, 15 * sr)
        section1 = 0.3 * np.sin(2 * np.pi * 220 * t1)
        
        # Section 2: Mid frequency (verse)
        t2 = np.linspace(0, 20, 20 * sr) 
        section2 = 0.5 * np.sin(2 * np.pi * 440 * t2)
        
        # Section 3: High frequency (chorus)
        t3 = np.linspace(0, 15, 15 * sr)
        section3 = 0.7 * np.sin(2 * np.pi * 880 * t3)
        
        # Section 4: Mixed frequencies (outro)
        t4 = np.linspace(0, 10, 10 * sr)
        section4 = 0.4 * (np.sin(2 * np.pi * 220 * t4) + 0.5 * np.sin(2 * np.pi * 440 * t4))
        
        # Combine sections
        audio = np.concatenate([section1, section2, section3, section4])
        
        # Save test file
        test_file = '/tmp/msaf_test_audio.wav'
        sf.write(test_file, audio, sr)
        
        print(f"✅ Created test audio: {test_file} ({len(audio)/sr:.1f}s)")
        return test_file, sr
        
    except Exception as e:
        print(f"❌ Could not create test audio: {e}")
        return None, None

def test_current_segmentation(audio_file):
    """Test current Sectionist segmentation"""
    if not SECTIONIST_AVAILABLE:
        return None
    
    try:
        print("\n🧪 Testing Current Sectionist Algorithm:")
        start_time = time.time()
        result = analyze_audio_file(audio_file)
        processing_time = time.time() - start_time
        
        sections = result.get('sections', [])
        print(f"   Detected {len(sections)} sections in {processing_time:.2f}s")
        
        for i, section in enumerate(sections[:5]):  # Limit output
            print(f"   {i+1}. {section.get('name', 'Unknown')}: {section.get('start', 0):.1f}s - {section.get('end', 0):.1f}s")
        
        return {
            'sections': sections,
            'processing_time': processing_time,
            'method': 'sectionist_current'
        }
        
    except Exception as e:
        print(f"   ❌ Current method failed: {e}")
        return None

def test_msaf_segmentation(audio_file):
    """Test MSAF segmentation"""
    try:
        import msaf
        
        print("\n🧪 Testing MSAF Algorithm:")
        start_time = time.time()
        
        # Test different MSAF algorithms
        algorithms = ['sf', 'cnmf', 'foote']  # Start with most reliable ones
        best_result = None
        
        for alg in algorithms:
            try:
                boundaries, labels = msaf.process(audio_file, 
                                                boundaries_id=alg, 
                                                labels_id='cnmf')
                
                # Convert to Sectionist format
                sections = []
                for i in range(len(boundaries) - 1):
                    sections.append({
                        'name': f"Section_{i+1}",
                        'start': boundaries[i],
                        'end': boundaries[i+1],
                        'confidence': 0.8,
                        'algorithm': alg
                    })
                
                processing_time = time.time() - start_time
                result = {
                    'sections': sections,
                    'processing_time': processing_time,
                    'method': f'msaf_{alg}'
                }
                
                if not best_result or len(sections) > len(best_result['sections']):
                    best_result = result
                
                print(f"   Algorithm '{alg}': {len(sections)} sections")
                
            except Exception as e:
                print(f"   Algorithm '{alg}' failed: {e}")
                continue
        
        if best_result:
            sections = best_result['sections']
            print(f"   Best result: {len(sections)} sections in {best_result['processing_time']:.2f}s")
            
            for i, section in enumerate(sections[:5]):  # Limit output
                print(f"   {i+1}. {section.get('name', 'Unknown')}: {section.get('start', 0):.1f}s - {section.get('end', 0):.1f}s")
            
            return best_result
        
        return None
        
    except Exception as e:
        print(f"   ❌ MSAF failed: {e}")
        traceback.print_exc()
        return None

def compare_results(current_result, msaf_result):
    """Compare segmentation results"""
    print("\n📊 Comparison Results:")
    
    if not current_result:
        print("   Current method: FAILED")
    else:
        current_sections = len(current_result.get('sections', []))
        current_time = current_result.get('processing_time', 0)
        print(f"   Current method: {current_sections} sections, {current_time:.2f}s")
    
    if not msaf_result:
        print("   MSAF method: FAILED")
    else:
        msaf_sections = len(msaf_result.get('sections', []))
        msaf_time = msaf_result.get('processing_time', 0)
        msaf_alg = msaf_result.get('method', 'unknown')
        print(f"   MSAF method ({msaf_alg}): {msaf_sections} sections, {msaf_time:.2f}s")
    
    # Simple quality assessment
    expected_sections = 4  # We created 4 distinct sections
    
    if current_result:
        current_accuracy = abs(expected_sections - len(current_result.get('sections', []))) / expected_sections
        print(f"   Current accuracy estimate: {(1-current_accuracy)*100:.1f}%")
    
    if msaf_result:
        msaf_accuracy = abs(expected_sections - len(msaf_result.get('sections', []))) / expected_sections  
        print(f"   MSAF accuracy estimate: {(1-msaf_accuracy)*100:.1f}%")

def main():
    """Main prototype testing function"""
    print("🔍 MSAF Integration Prototype for Sectionist")
    print("=" * 50)
    
    # Check dependencies
    msaf_available = test_msaf_availability()
    
    if not msaf_available:
        print("\n💡 To test MSAF integration:")
        print("   1. pip install msaf")  
        print("   2. Run this script again")
        return
    
    # Create test audio
    test_file, sr = create_test_audio()
    if not test_file:
        return
    
    print(f"\nExpected structure: 4 sections (intro 15s, verse 20s, chorus 15s, outro 10s)")
    
    # Test current method
    current_result = test_current_segmentation(test_file)
    
    # Test MSAF
    msaf_result = test_msaf_segmentation(test_file)
    
    # Compare
    compare_results(current_result, msaf_result)
    
    # Conclusions
    print("\n🎯 Prototype Conclusions:")
    if msaf_result and current_result:
        print("   ✅ MSAF integration is feasible")
        print("   ✅ Both algorithms can run on same audio")
        print("   💡 Hybrid approach would use best result from each")
    elif msaf_result:
        print("   ✅ MSAF works when current method fails")
        print("   💡 MSAF could serve as fallback algorithm")
    else:
        print("   ⚠️  Need to debug MSAF setup")
    
    print(f"\n🧹 Cleanup: rm {test_file}")
    try:
        os.remove(test_file)
    except:
        pass

if __name__ == "__main__":
    main()