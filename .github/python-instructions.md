---
description: 'Python coding standards and best practices for Sectionist'
applyTo: '**/*.py'
---

# Python Development Standards for Sectionist

## Code Style and Formatting

### PEP 8 Compliance
- Follow **PEP 8** style guide strictly
- Use 4 spaces for indentation (no tabs)
- Maintain line length of 79 characters maximum
- Use proper spacing around operators and after commas
- Follow naming conventions:
  - `snake_case` for functions, variables, and module names
  - `PascalCase` for class names
  - `UPPER_CASE` for constants

### Import Organization
```python
# Standard library imports first
import os
import sys
import tempfile
from typing import Dict, List, Optional, Tuple

# Third-party imports second
import numpy as np
import librosa
from flask import Flask, request, jsonify
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget

# Local application imports last
from .audio_analysis import analyze_sections
from .exceptions import AudioProcessingError
```

### Type Hints and Annotations
```python
# Always include type hints for function parameters and return values
def analyze_audio_file(
    file_path: str, 
    sample_rate: int = 22050,
    hop_length: int = 512
) -> Dict[str, Any]:
    """
    Analyze audio file and return structured results.
    
    Args:
        file_path: Path to the audio file to analyze
        sample_rate: Target sample rate for analysis (default: 22050)
        hop_length: Number of samples between frames (default: 512)
        
    Returns:
        Dictionary containing analysis results with keys:
        - 'sections': List of detected sections
        - 'key': Detected musical key
        - 'tempo': Estimated tempo in BPM
        - 'duration': Audio duration in seconds
        
    Raises:
        AudioProcessingError: If audio analysis fails
        FileNotFoundError: If audio file doesn't exist
    """
```

## Documentation Standards

### Docstring Format
Use Google-style docstrings for consistency:

```python
def detect_song_sections(
    audio_data: np.ndarray, 
    sr: int, 
    threshold: float = 0.1
) -> List[Dict[str, Any]]:
    """Detect song sections using spectral analysis.
    
    This function analyzes the audio signal to identify structural boundaries
    in music, such as verse, chorus, and bridge sections.
    
    Args:
        audio_data: Audio time series as numpy array
        sr: Sample rate of audio data
        threshold: Sensitivity threshold for boundary detection (0.0-1.0)
        
    Returns:
        List of sections, each containing:
            - start_time: Section start in seconds
            - end_time: Section end in seconds  
            - label: Section type (e.g., 'verse', 'chorus')
            - confidence: Detection confidence (0.0-1.0)
            
    Raises:
        ValueError: If threshold is not between 0.0 and 1.0
        AudioProcessingError: If section detection fails
        
    Example:
        >>> y, sr = librosa.load('song.mp3')
        >>> sections = detect_song_sections(y, sr, threshold=0.2)
        >>> print(f"Found {len(sections)} sections")
    """
```

### Inline Comments
- Explain complex algorithms and non-obvious code
- Document audio processing parameters and their effects
- Include references to academic papers or algorithms used
- Explain business logic and musical concepts

```python
# Apply harmonic-percussive separation to isolate melodic content
# This helps improve key detection accuracy by reducing drum interference
y_harmonic = librosa.effects.harmonic(y, margin=8.0)

# Use Krumhansl-Schmuckler key-finding algorithm
# Based on correlation with major/minor key profiles
chroma = librosa.feature.chroma_stft(y=y_harmonic, sr=sr)
```

## Error Handling Patterns

### Custom Exceptions
```python
# Define domain-specific exceptions
class SectionistError(Exception):
    """Base exception for Sectionist application."""
    pass

class AudioProcessingError(SectionistError):
    """Raised when audio processing fails."""
    pass

class UnsupportedFormatError(AudioProcessingError):
    """Raised for unsupported audio formats."""
    pass

class BackendConnectionError(SectionistError):
    """Raised when backend communication fails."""
    pass
```

### Exception Handling Best Practices
```python
def load_and_analyze_audio(file_path: str) -> Dict[str, Any]:
    """Load audio file and perform analysis with proper error handling."""
    try:
        # Load audio with librosa
        y, sr = librosa.load(file_path, sr=22050)
        
        # Validate audio data
        if len(y) == 0:
            raise AudioProcessingError("Audio file is empty")
            
        # Perform analysis
        result = perform_analysis(y, sr)
        return result
        
    except FileNotFoundError:
        logger.error(f"Audio file not found: {file_path}")
        raise
    except librosa.LibrosaError as e:
        logger.error(f"Librosa error processing {file_path}: {e}")
        raise AudioProcessingError(f"Failed to process audio: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing {file_path}: {e}")
        raise AudioProcessingError(f"Audio analysis failed: {e}")
```

## Logging Standards

### Logger Configuration
```python
import logging

# Configure module-level logger
logger = logging.getLogger(__name__)

# Use structured logging for audio analysis
def analyze_with_logging(file_path: str) -> Dict[str, Any]:
    """Analyze audio file with comprehensive logging."""
    logger.info(f"Starting analysis", extra={
        'file_path': file_path,
        'file_size': os.path.getsize(file_path)
    })
    
    start_time = time.time()
    
    try:
        result = perform_analysis(file_path)
        
        duration = time.time() - start_time
        logger.info(f"Analysis completed successfully", extra={
            'file_path': file_path,
            'duration_seconds': duration,
            'sections_found': len(result.get('sections', []))
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Analysis failed", extra={
            'file_path': file_path,
            'error': str(e),
            'duration_seconds': time.time() - start_time
        })
        raise
```

## Audio Processing Best Practices

### Librosa Usage Patterns
```python
def load_audio_consistently(file_path: str) -> Tuple[np.ndarray, int]:
    """Load audio with consistent parameters for analysis."""
    # Use consistent sample rate for all analysis
    SR = 22050
    
    # Load with mono conversion and normalization
    y, sr = librosa.load(
        file_path,
        sr=SR,
        mono=True,
        normalize=True
    )
    
    # Validate audio properties
    if len(y) < SR:  # Less than 1 second
        logger.warning(f"Audio file is very short: {len(y)/SR:.2f} seconds")
        
    return y, sr

def extract_audio_features(y: np.ndarray, sr: int) -> Dict[str, np.ndarray]:
    """Extract comprehensive audio features for analysis."""
    features = {}
    
    # Spectral features
    features['mfcc'] = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    features['chroma'] = librosa.feature.chroma_stft(y=y, sr=sr)
    features['spectral_centroid'] = librosa.feature.spectral_centroid(y=y, sr=sr)
    
    # Rhythmic features
    features['tempo'], features['beats'] = librosa.beat.beat_track(y=y, sr=sr)
    features['onset_envelope'] = librosa.onset.onset_strength(y=y, sr=sr)
    
    return features
```

### Memory Management
```python
def process_large_audio_file(file_path: str) -> Dict[str, Any]:
    """Process large audio files with memory management."""
    # Use streaming for very large files
    if os.path.getsize(file_path) > 100 * 1024 * 1024:  # 100MB
        return process_audio_streaming(file_path)
    
    try:
        y, sr = librosa.load(file_path)
        result = analyze_audio(y, sr)
        
        # Explicitly delete large arrays to free memory
        del y
        
        return result
        
    except MemoryError:
        logger.warning(f"Memory error with {file_path}, trying streaming approach")
        return process_audio_streaming(file_path)
```

## PyQt6 Development Patterns

### Signal-Slot Best Practices
```python
class AnalysisWorker(QThread):
    """Worker thread for background audio analysis."""
    
    # Define signals with descriptive names and proper types
    progress_updated = pyqtSignal(int)  # Progress percentage (0-100)
    section_detected = pyqtSignal(str, float, float)  # label, start, end
    analysis_completed = pyqtSignal(dict)  # Complete results
    error_occurred = pyqtSignal(str)  # Error message
    
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._is_cancelled = False
        
    def run(self):
        """Main thread execution with progress reporting."""
        try:
            self.progress_updated.emit(10)
            
            # Load audio
            y, sr = librosa.load(self.file_path)
            self.progress_updated.emit(30)
            
            if self._is_cancelled:
                return
                
            # Analyze sections
            sections = self.detect_sections(y, sr)
            self.progress_updated.emit(70)
            
            # Detect key and tempo
            key = self.detect_key(y, sr)
            tempo = self.detect_tempo(y, sr)
            self.progress_updated.emit(90)
            
            result = {
                'sections': sections,
                'key': key,
                'tempo': tempo
            }
            
            self.progress_updated.emit(100)
            self.analysis_completed.emit(result)
            
        except Exception as e:
            logger.error(f"Analysis worker error: {e}")
            self.error_occurred.emit(str(e))
            
    def cancel(self):
        """Cancel the analysis operation."""
        self._is_cancelled = True
```

### Resource Management
```python
class AudioPlayer(QObject):
    """Audio player with proper resource management."""
    
    def __init__(self):
        super().__init__()
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        
    def __del__(self):
        """Clean up VLC resources."""
        if hasattr(self, 'player'):
            self.player.stop()
            self.player.release()
        if hasattr(self, 'vlc_instance'):
            self.vlc_instance.release()
            
    def load_file(self, file_path: str):
        """Load audio file with error handling."""
        try:
            media = self.vlc_instance.media_new(file_path)
            self.player.set_media(media)
            
            # Wait for media to be parsed
            media.parse_with_options(vlc.MediaParseFlag.local, 0)
            
        except Exception as e:
            logger.error(f"Failed to load audio file {file_path}: {e}")
            raise AudioPlayerError(f"Cannot load audio: {e}")
```

## Testing Patterns

### Unit Testing
```python
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

class TestAudioAnalysis:
    """Test suite for audio analysis functions."""
    
    @pytest.fixture
    def sample_audio(self):
        """Generate test audio data."""
        duration = 5.0  # 5 seconds
        sr = 22050
        t = np.linspace(0, duration, int(sr * duration))
        # Generate a simple sine wave
        y = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        return y, sr
        
    def test_section_detection(self, sample_audio):
        """Test section detection with known audio."""
        y, sr = sample_audio
        sections = detect_song_sections(y, sr)
        
        assert isinstance(sections, list)
        assert len(sections) > 0
        
        # Verify section structure
        for section in sections:
            assert 'start_time' in section
            assert 'end_time' in section
            assert 'label' in section
            assert section['start_time'] < section['end_time']
            
    @patch('librosa.load')
    def test_file_loading_error(self, mock_load):
        """Test error handling for file loading."""
        mock_load.side_effect = librosa.LibrosaError("Mock error")
        
        with pytest.raises(AudioProcessingError):
            load_and_analyze_audio('nonexistent.mp3')
```

### Integration Testing
```python
def test_backend_api_integration():
    """Test complete backend API workflow."""
    # Test with actual audio file
    test_file = 'tests/data/test_audio.wav'
    
    with open(test_file, 'rb') as f:
        response = requests.post(
            'http://localhost:5000/analyze',
            files={'file': f}
        )
    
    assert response.status_code == 200
    
    result = response.json()
    assert 'sections' in result
    assert 'key' in result
    assert 'tempo' in result
    assert isinstance(result['sections'], list)
```

## Configuration Management

### Environment-Based Configuration
```python
import os
from typing import Optional

class Config:
    """Application configuration with environment variable support."""
    
    # Backend configuration
    BACKEND_HOST: str = os.getenv('BACKEND_HOST', '127.0.0.1')
    BACKEND_PORT: int = int(os.getenv('BACKEND_PORT', '5000'))
    
    # Audio processing configuration
    DEFAULT_SAMPLE_RATE: int = int(os.getenv('SAMPLE_RATE', '22050'))
    MAX_FILE_SIZE: int = int(os.getenv('MAX_FILE_SIZE', '104857600'))  # 100MB
    
    # Analysis parameters
    SECTION_THRESHOLD: float = float(os.getenv('SECTION_THRESHOLD', '0.1'))
    KEY_CONFIDENCE_THRESHOLD: float = float(os.getenv('KEY_CONFIDENCE', '0.7'))
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: Optional[str] = os.getenv('LOG_FILE')
    
    @property
    def backend_url(self) -> str:
        """Get complete backend URL."""
        return f"http://{self.BACKEND_HOST}:{self.BACKEND_PORT}"
```

## Performance Optimization

### Efficient Numpy Operations
```python
def efficient_audio_processing(y: np.ndarray, sr: int) -> Dict[str, Any]:
    """Optimize audio processing for performance."""
    # Pre-allocate arrays when size is known
    n_frames = len(y) // 512
    features = np.zeros((13, n_frames))
    
    # Use vectorized operations instead of loops
    # Good: vectorized operation
    rms = librosa.feature.rms(y=y)[0]
    
    # Avoid: manual loop
    # rms = np.array([np.sqrt(np.mean(frame**2)) for frame in frames])
    
    # Use appropriate data types
    tempo_float32 = np.float32(tempo)  # Use float32 for tempo
    
    return {
        'rms': rms,
        'tempo': tempo_float32
    }
```

### Caching Strategies
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_key_template(key_name: str) -> np.ndarray:
    """Cache key templates for repeated use."""
    # Generate or load key template
    return generate_key_template(key_name)

# Use weak references for audio data caching
import weakref

class AudioCache:
    """Weak reference cache for audio data."""
    
    def __init__(self):
        self._cache = weakref.WeakValueDictionary()
        
    def get_audio(self, file_path: str) -> Optional[np.ndarray]:
        """Get cached audio data if available."""
        return self._cache.get(file_path)
        
    def cache_audio(self, file_path: str, audio_data: np.ndarray):
        """Cache audio data with weak reference."""
        self._cache[file_path] = audio_data
```