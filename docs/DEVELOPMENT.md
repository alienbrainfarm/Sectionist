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

Sectionist uses a unified Python architecture with a cross-platform PyQt6 frontend and a Python backend:

```
┌─────────────────┐    HTTP API     ┌─────────────────┐
│                 │◄──────────────►│                 │
│ Python Frontend │                │ Python Backend  │
│  (PyQt6 GUI)    │                │ (Audio Analysis)│
│ Windows/macOS/  │                │                 │
│     Linux       │                │                 │
└─────────────────┘                └─────────────────┘
         │                                   │
         ▼                                   ▼
┌─────────────────┐                ┌─────────────────┐
│   Audio Files   │                │   ML Models     │
│   (Local)       │                │   (Local)       │
└─────────────────┘                └─────────────────┘
```

### Key Design Decisions

- **Cross-Platform**: Runs on Windows, macOS, and Linux
- **Local Processing**: All audio analysis happens locally for privacy
- **Unified Language**: Both frontend and backend use Python for easier maintenance
- **Asynchronous Communication**: Non-blocking audio analysis
- **HTTP API**: RESTful communication between components

## Frontend Development

### Python/PyQt6 Project Structure (Current Active Development)

```
frontend/
├── sectionist_gui.py              # Application entry point ✅ IMPLEMENTED
├── main_window.py                 # Main window and UI logic ✅ IMPLEMENTED
├── timeline_widget.py             # Timeline visualization ✅ IMPLEMENTED
├── audio_player.py                # python-vlc audio playback ✅ IMPLEMENTED
├── analysis_worker.py             # Background analysis worker ✅ IMPLEMENTED
├── requirements.txt               # Dependencies ✅ IMPLEMENTED
├── setup.sh                       # Setup script ✅ IMPLEMENTED
├── conftest.py                    # Headless Qt test configuration ✅ IMPLEMENTED
└── README.md                      # Documentation ✅ IMPLEMENTED
```

### Development Setup

1. **Install Python 3.8+**
2. **Set up virtual environment**:
   ```bash
   cd frontend/
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Install the VLC media player** (provides the `libvlc` library required by
   python-vlc)
5. **Run the application**:
   ```bash
   python sectionist_gui.py
   ```

## Backend Development

### Python Project Structure (Current Implementation)

```
backend/
├── requirements.txt              # Production dependencies ✅ IMPLEMENTED
├── requirements-dev.txt          # Development dependencies ✅ IMPLEMENTED
├── server.py                     # Flask HTTP server ✅ IMPLEMENTED
├── example.py                    # Core analysis algorithms ✅ IMPLEMENTED
├── start_server.sh              # Server startup script ✅ IMPLEMENTED
├── setup.sh                     # Environment setup script ✅ IMPLEMENTED
├── pytest.ini                   # Test configuration ✅ IMPLEMENTED
├── test_audio_analysis.py       # Audio analysis tests ✅ IMPLEMENTED
├── test_segmentation.py         # Segmentation tests ✅ IMPLEMENTED
├── test_server.py               # API endpoint tests ✅ IMPLEMENTED
├── coverage.xml                 # Test coverage report ✅ IMPLEMENTED
├── .gitignore                   # Git ignore rules ✅ IMPLEMENTED
└── README.md                    # Backend documentation ✅ IMPLEMENTED
```

**Note**: The current implementation uses a simpler, flatter structure focused on rapid prototyping and development, with all functionality consolidated into fewer files rather than the originally planned modular package structure.

### Core Dependencies

```python
# requirements.txt
librosa>=0.10.0
numpy>=1.24.0
scipy>=1.10.0
flask>=2.3.0
pytest>=7.0.0
requests>=2.31.0

# Optional (commented out in requirements.txt)
# madmom>=0.16.1
# essentia>=2.1b1
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
python server.py
```

## Communication Protocol

### Frontend-Backend Communication

1. **HTTP REST API** (Primary):
   - Frontend makes HTTP requests to local backend
   - JSON payload for requests/responses
   - Requests run in a background worker thread in the PyQt6 frontend

2. **File-based Exchange** (Alternative):
   - Frontend writes audio file path to shared location
   - Backend processes and writes results to JSON file
   - Frontend polls for completion

### Example Python Client

```python
import requests

def analyze_audio(file_path: str) -> dict:
    """Upload an audio file to the local backend and return the analysis."""
    with open(file_path, "rb") as audio:
        response = requests.post(
            "http://127.0.0.1:5000/analyze",
            files={"audio": audio},
        )
    response.raise_for_status()
    return response.json()
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

1. **Unit Tests** (pytest):
   ```bash
   cd frontend
   QT_QPA_PLATFORM=offscreen pytest -v
   ```
   Tests cover the window structure, timeline widget, and backend
   integration (`test_gui_structure.py`, `test_integration.py`,
   `test_timeline_improvements.py`).

2. **UI Tests**:
   - Construct PyQt6 widgets directly and assert their structure
   - Run headless in CI with `QT_QPA_PLATFORM=offscreen`

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
   - Use Qt painting primitives efficiently

## Deployment

### Development Deployment

1. **Backend**:
   ```bash
   # Run the Flask development server
   python server.py
   ```

2. **Frontend**:
   ```bash
   # Run the PyQt6 application directly
   python sectionist_gui.py
   ```

### Production Considerations

1. **Backend Packaging**:
   - Consider PyInstaller for standalone executable
   - Bundle ML models with application

2. **Desktop App Distribution**:
   - Package the PyQt6 frontend with PyInstaller
   - Ensure the VLC media player (libvlc) is available on the target machine
   - Consider platform-specific installers

### CI/CD Pipeline

CI runs on GitHub Actions via `.github/workflows/ci.yml`, with three jobs:

- **Backend (Python 3.10/3.11/3.12)** - flake8, `black --check`, and
  pytest with coverage
- **Frontend** - headless PyQt6 tests on Ubuntu with Qt and libvlc installed
- **Integration** - starts the Flask server, waits for `/health`, and runs
  `backend/smoke_test.py` end to end

See [CI/CD Pipeline](CI_CD.md) for details.

## Next Steps

1. **Refine Project Structure**: Keep the Python backend and frontend packages organized
2. **Implement Audio Loading**: Basic audio file handling
3. **Prototype Segmentation**: Simple section detection algorithm
4. **Frontend-Backend Integration**: Establish communication protocol
5. **UI Development**: Timeline visualization and interaction
6. **Testing Infrastructure**: Unit and integration tests
7. **Performance Optimization**: Profiling and optimization
8. **Documentation**: User guides and API documentation

For questions or clarification on any of these topics, please open an issue or discussion on GitHub.