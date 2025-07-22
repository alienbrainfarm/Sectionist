#!/usr/bin/env python3
"""
Test script for Python frontend backend integration.

This script tests the integration between the Python frontend
and the existing Flask backend without requiring a GUI.
"""

import sys
import requests
import json
import time
from pathlib import Path

def test_backend_health():
    """Test if the backend server is responding."""
    print("Testing backend health...")
    try:
        response = requests.get("http://127.0.0.1:5000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy: {data}")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is it running on port 5000?")
        return False
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        return False

def test_supported_formats():
    """Test the supported formats endpoint."""
    print("\nTesting supported formats...")
    try:
        response = requests.get("http://127.0.0.1:5000/formats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            formats = data.get('supported_formats', [])
            print(f"✅ Supported formats: {', '.join(formats)}")
            return True
        else:
            print(f"❌ Formats endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing formats: {e}")
        return False

def simulate_file_analysis():
    """Simulate file analysis by testing with a dummy file."""
    print("\nTesting analysis endpoint with dummy data...")
    
    # Create a small dummy audio file (just bytes for testing)
    dummy_audio_data = b"dummy audio data for testing"
    
    try:
        files = {'audio': ('test.mp3', dummy_audio_data, 'audio/mp3')}
        response = requests.post(
            "http://127.0.0.1:5000/analyze",
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Analysis endpoint accepts requests")
                analysis = data.get('analysis', {})
                print(f"   Duration: {analysis.get('duration', 'N/A')}")
                print(f"   Tempo: {analysis.get('tempo', 'N/A')}")
                print(f"   Key: {analysis.get('key', 'N/A')}")
                return True
            else:
                error = data.get('error', 'Unknown error')
                print(f"⚠️ Analysis failed (expected with dummy data): {error}")
                return True  # This is expected with dummy data
        else:
            print(f"❌ Analysis endpoint returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing analysis: {e}")
        return False

def test_python_frontend_imports():
    """Test if the Python frontend dependencies can be imported."""
    print("\nTesting Python frontend imports...")
    
    # Test standard library imports
    try:
        import tkinter
        print("✅ tkinter available (for minimal_demo.py)")
    except ImportError:
        print("⚠️ tkinter not available (expected in headless environments)")
    
    try:
        import requests
        print("✅ requests available")
    except ImportError:
        print("❌ requests not available - install with: pip install requests")
        return False
    
    try:
        import threading
        import json
        import sys
        from pathlib import Path
        from typing import Dict, Optional
        print("✅ Standard library imports working")
    except ImportError as e:
        print(f"❌ Standard library import error: {e}")
        return False
    
    # Test PyQt6 (optional)
    try:
        from PyQt6.QtWidgets import QApplication
        print("✅ PyQt6 available (for sectionist_gui.py)")
    except ImportError:
        print("⚠️ PyQt6 not available - install with: pip install PyQt6")
    
    return True

def generate_integration_report():
    """Generate a comprehensive integration report."""
    print("\n" + "="*60)
    print("PYTHON FRONTEND INTEGRATION REPORT")
    print("="*60)
    
    results = {
        'backend_health': test_backend_health(),
        'supported_formats': test_supported_formats(), 
        'analysis_endpoint': simulate_file_analysis(),
        'python_imports': test_python_frontend_imports()
    }
    
    print(f"\nSUMMARY:")
    print("-" * 30)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False
    
    print("-" * 30)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED - Python frontend is ready for integration!")
        print("\nNext steps:")
        print("1. Start the backend: cd backend && ./start_server.sh")
        print("2. Run Python frontend: cd frontend-python && python minimal_demo.py")
        print("3. Test with real audio files")
    else:
        print("⚠️  Some tests failed - check the issues above")
        print("\nTroubleshooting:")
        if not results['backend_health']:
            print("- Start backend: cd backend && ./start_server.sh")
        if not results['python_imports']:
            print("- Install dependencies: pip install requests PyQt6")
    
    return all_passed

def main():
    """Main function."""
    print("Sectionist Python Frontend Integration Test")
    print("==========================================")
    print()
    print("This script validates the integration between the Python frontend")
    print("and the existing Flask backend to ensure compatibility.")
    print()
    
    success = generate_integration_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())