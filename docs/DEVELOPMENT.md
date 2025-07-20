# Development Guide

This guide provides detailed information for setting up and developing Sectionist.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Frontend Development](#frontend-development)
- [Backend Development](#backend-development)
- [Communication Protocol](#communication-protocol)
- [Audio Processing Pipeline](#audio-processing-pipeline)
- [Testing Strategy](#testing-strategy)
- [Performance Considerations](#performance-considerations)
- [Deployment](#deployment)

## Architecture Overview

Sectionist uses a hybrid architecture with a native SwiftUI frontend and a Python backend:

```
┌─────────────────┐    HTTP/IPC     ┌─────────────────┐
│                 │◄──────────────►│                 │
│  SwiftUI Frontend│                │ Python Backend  │
│   (macOS App)   │                │ (Audio Analysis)│
│                 │                │                 │
└─────────────────┘                └─────────────────┘
         │                                   │
         ▼                                   ▼
┌─────────────────┐                ┌─────────────────┐
│   Audio Files   │                │   ML Models     │
│   (Local)       │                │   (Local)       │
└─────────────────┘                └─────────────────┘
```

### Key Design Decisions

- **Local Processing**: All audio analysis happens locally for privacy
- **Separation of Concerns**: UI logic in Swift, audio processing in Python
- **Asynchronous Communication**: Non-blocking audio analysis
- **File-based Exchange**: Minimal data transfer between frontend and backend

## Frontend Development

### SwiftUI Project Structure

```
Sectionist/
├── Sectionist.xcodeproj
├── Sources/
│   ├── SectionistApp.swift           # App entry point
│   ├── Views/
│   │   ├── ContentView.swift         # Main view
│   │   ├── AudioTimelineView.swift   # Timeline visualization
│   │   ├── SectionDetailView.swift   # Section editing
│   │   └── SettingsView.swift        # App settings
│   ├── Models/
│   │   ├── AudioFile.swift           # Audio file representation
│   │   ├── SongAnalysis.swift        # Analysis results
│   │   └── Section.swift             # Song section model
│   ├── Services/
│   │   ├── AudioService.swift        # Audio file handling
│   │   ├── AnalysisService.swift     # Backend communication
│   │   └── ExportService.swift       # Export functionality
│   └── Utilities/
│       ├── AudioUtilities.swift      # Audio helper functions
│       └── Extensions.swift          # Swift extensions
├── Tests/
│   ├── SectionistTests/
│   └── SectionistUITests/
└── Resources/
    ├── Assets.xcassets
    └── sample_audio/
```

### Key SwiftUI Components

#### AudioTimelineView
- Displays song sections on a timeline
- Handles user interaction for section editing
- Shows waveform visualization

#### SongAnalysis Model
```swift
struct SongAnalysis: Codable {
    let duration: TimeInterval
    let key: String
    let tempo: Double
    let sections: [Section]
    let chords: [Chord]?
}

struct Section: Codable, Identifiable {
    let id = UUID()
    let label: String
    let startTime: TimeInterval
    let endTime: TimeInterval
    let confidence: Double
}
```

### Development Setup

1. **Xcode Requirements**:
   - Xcode 14.0+ 
   - macOS deployment target: 12.0+
   - Swift 5.7+

2. **Dependencies**:
   - No external Swift packages initially
   - Consider adding later: Charts framework for visualization

3. **Build Configuration**:
   ```bash
   cd Sectionist/
   open Sectionist.xcodeproj
   
   # Build for development
   xcodebuild -scheme Sectionist -configuration Debug
   
   # Run tests
   xcodebuild test -scheme Sectionist
   ```

## Backend Development

### Python Project Structure

```
backend/
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── src/
│   ├── sectionist/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── server.py            # HTTP server
│   │   │   └── handlers.py          # Request handlers
│   │   ├── audio/
│   │   │   ├── __init__.py
│   │   │   ├── loader.py            # Audio file loading
│   │   │   ├── preprocessing.py     # Audio preprocessing
│   │   │   └── features.py          # Feature extraction
│   │   ├── analysis/
│   │   │   ├── __init__.py
│   │   │   ├── segmentation.py      # Section detection
│   │   │   ├── key_detection.py     # Key analysis
│   │   │   └── chord_detection.py   # Chord recognition
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── ml_models.py         # ML model loading
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── helpers.py           # Utility functions
├── tests/
│   ├── test_audio/
│   ├── test_analysis/
│   └── test_api/
├── models/                          # Pre-trained models
└── data/
    └── sample_audio/
```

### Core Dependencies

```python
# requirements.txt
librosa>=0.10.0
numpy>=1.21.0
scipy>=1.9.0
scikit-learn>=1.1.0
fastapi>=0.100.0
uvicorn>=0.20.0
pydantic>=2.0.0
python-multipart>=0.0.6

# Optional but recommended
madmom>=0.16.1
essentia>=2.1b6.dev858
```

### Development Dependencies

```python
# requirements-dev.txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
black>=22.0.0
flake8>=5.0.0
mypy>=1.0.0
coverage>=7.0.0
pre-commit>=3.0.0
```

### API Design

#### RESTful Endpoints

```python
# POST /analyze
{
    "audio_file": "path/to/audio.mp3",
    "options": {
        "analyze_sections": true,
        "analyze_key": true,
        "analyze_chords": true
    }
}

# Response
{
    "status": "success",
    "analysis": {
        "duration": 180.5,
        "key": "C major",
        "tempo": 120.0,
        "sections": [...],
        "chords": [...]
    }
}
```

### Environment Setup

```bash
cd backend/

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .

# Run development server
uvicorn sectionist.api.server:app --reload --host 127.0.0.1 --port 8000
```

## Communication Protocol

### Frontend-Backend Communication

1. **HTTP REST API** (Primary):
   - Frontend makes HTTP requests to local backend
   - JSON payload for requests/responses
   - Async/await pattern in Swift

2. **File-based Exchange** (Alternative):
   - Frontend writes audio file path to shared location
   - Backend processes and writes results to JSON file
   - Frontend polls for completion

### Example Swift Service

```swift
class AnalysisService: ObservableObject {
    private let baseURL = URL(string: "http://127.0.0.1:8000")!
    
    func analyzeAudio(_ audioURL: URL) async throws -> SongAnalysis {
        // Implementation
    }
}
```

## Audio Processing Pipeline

### 1. Audio Loading and Preprocessing

```python
import librosa

def load_audio(file_path: str) -> tuple[np.ndarray, int]:
    """Load audio file and return audio data and sample rate."""
    y, sr = librosa.load(file_path, sr=22050)
    return y, sr

def preprocess_audio(y: np.ndarray, sr: int) -> np.ndarray:
    """Normalize and clean audio data."""
    # Normalize
    y = librosa.util.normalize(y)
    # Apply pre-emphasis filter if needed
    return y
```

### 2. Feature Extraction

```python
def extract_features(y: np.ndarray, sr: int) -> dict:
    """Extract audio features for analysis."""
    features = {}
    
    # Spectral features
    features['mfcc'] = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    features['chroma'] = librosa.feature.chroma(y=y, sr=sr)
    features['spectral_centroid'] = librosa.feature.spectral_centroid(y=y, sr=sr)
    
    # Temporal features
    features['tempo'] = librosa.beat.tempo(y=y, sr=sr)[0]
    features['beats'] = librosa.beat.beat_track(y=y, sr=sr)[1]
    
    return features
```

### 3. Section Segmentation

```python
def segment_audio(y: np.ndarray, sr: int) -> list[dict]:
    """Detect song sections using audio similarity."""
    # Extract chroma features for harmonic analysis
    chroma = librosa.feature.chroma(y=y, sr=sr, hop_length=512)
    
    # Compute self-similarity matrix
    similarity = librosa.segment.cross_similarity(chroma, chroma)
    
    # Detect boundaries
    boundaries = librosa.segment.agglomerative(similarity, k=5)
    
    # Convert to time stamps
    boundary_times = librosa.frames_to_time(boundaries, sr=sr, hop_length=512)
    
    # Create sections
    sections = []
    for i, start in enumerate(boundary_times[:-1]):
        sections.append({
            'start': float(start),
            'end': float(boundary_times[i + 1]),
            'label': f'Section {i + 1}'
        })
    
    return sections
```

## Testing Strategy

### Frontend Tests

1. **Unit Tests** (XCTest):
   ```swift
   func testAudioFileLoading() {
       let service = AudioService()
       // Test audio file validation
   }
   ```

2. **UI Tests**:
   ```swift
   func testTimelineInteraction() {
       let app = XCUIApplication()
       // Test timeline view interactions
   }
   ```

### Backend Tests

1. **Unit Tests** (pytest):
   ```python
   def test_audio_loading():
       """Test audio file loading functionality."""
       y, sr = load_audio("test_audio.wav")
       assert len(y) > 0
       assert sr == 22050
   
   def test_segmentation():
       """Test section segmentation algorithm."""
       sections = segment_audio(test_audio, test_sr)
       assert len(sections) > 0
   ```

2. **Integration Tests**:
   ```python
   @pytest.mark.asyncio
   async def test_analysis_endpoint():
       """Test complete analysis pipeline."""
       # Test API endpoint with sample audio
   ```

### Test Data

- Include sample audio files in various formats
- Test with different genres and lengths
- Include edge cases (very short/long files, silence, etc.)

## Performance Considerations

### Backend Optimization

1. **Audio Processing**:
   - Use appropriate sample rates (22kHz for analysis)
   - Implement chunked processing for long files
   - Cache feature extractions

2. **Memory Management**:
   ```python
   # Process audio in chunks to avoid memory issues
   def process_long_audio(y: np.ndarray, chunk_size: int = 1048576):
       for i in range(0, len(y), chunk_size):
           chunk = y[i:i + chunk_size]
           yield process_chunk(chunk)
   ```

### Frontend Optimization

1. **UI Responsiveness**:
   - Use async/await for backend calls
   - Show progress indicators for long operations
   - Implement proper loading states

2. **Audio Visualization**:
   - Downsample waveforms for display
   - Use Core Graphics efficiently

## Deployment

### Development Deployment

1. **Backend**:
   ```bash
   # Run with hot reload
   uvicorn sectionist.api.server:app --reload
   ```

2. **Frontend**:
   ```bash
   # Run in Xcode or build for distribution
   xcodebuild archive -scheme Sectionist
   ```

### Production Considerations

1. **Backend Packaging**:
   - Consider PyInstaller for standalone executable
   - Bundle ML models with application

2. **macOS App Distribution**:
   - Code signing for distribution
   - Notarization for macOS Gatekeeper
   - Consider Mac App Store distribution

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt -r requirements-dev.txt
      - name: Run tests
        run: |
          cd backend
          pytest
          
  test-frontend:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and test
        run: |
          cd Sectionist
          xcodebuild test -scheme Sectionist
```

## Next Steps

1. **Create Project Structure**: Set up Xcode project and Python package
2. **Implement Audio Loading**: Basic audio file handling
3. **Prototype Segmentation**: Simple section detection algorithm
4. **Frontend-Backend Integration**: Establish communication protocol
5. **UI Development**: Timeline visualization and interaction
6. **Testing Infrastructure**: Unit and integration tests
7. **Performance Optimization**: Profiling and optimization
8. **Documentation**: User guides and API documentation

For questions or clarification on any of these topics, please open an issue or discussion on GitHub.