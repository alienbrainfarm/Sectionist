---
description: 'Python backend development for audio analysis API'
applyTo: 'backend/**/*.py'
---

# Sectionist Backend Development Instructions

## Backend Architecture

The Sectionist backend is a Flask HTTP server that provides REST API endpoints for audio analysis. It uses librosa for music information retrieval and audio signal processing.

## Core Technologies

### Audio Processing Stack
- **librosa**: Primary library for audio feature extraction and analysis
- **numpy**: Numerical computations and array operations
- **scipy**: Scientific computing and signal processing
- **Flask**: Web framework for REST API endpoints

### Key Audio Analysis Features
- Song structure segmentation (intro, verse, chorus, bridge, outro)
- Key detection and harmonic analysis
- Tempo estimation and beat tracking
- Basic chord progression mapping
- Audio feature extraction (MFCC, spectrograms, chroma features)

## API Design Patterns

### Endpoint Structure
```python
@app.route("/analyze", methods=["POST"])
def analyze_audio():
    """
    Main analysis endpoint that accepts audio files and returns structured results.
    
    Expected file formats: MP3, WAV, AIFF, M4A, FLAC, OGG, AAC
    Maximum file size: 100MB
    
    Returns:
    {
        "sections": [...],
        "key": "C major",
        "tempo": 120.0,
        "duration": 180.5,
        "chords": [...]
    }
    """
```

### Error Handling
- Return appropriate HTTP status codes (400 for client errors, 500 for server errors)
- Provide descriptive error messages for different failure scenarios
- Log detailed error information for debugging
- Handle file upload validation and corrupted audio files

### File Processing
- Use secure filename handling with `werkzeug.utils.secure_filename`
- Store uploaded files in secure temporary locations
- Clean up temporary files after analysis
- Validate file extensions and MIME types

## Audio Analysis Implementation

### Librosa Best Practices
```python
# Standard audio loading with error handling
def load_audio_safely(file_path: str, sr: int = 22050) -> Tuple[np.ndarray, int]:
    """
    Load audio file with consistent sample rate and error handling.
    
    Args:
        file_path: Path to audio file
        sr: Target sample rate (22050 Hz is good for analysis)
    
    Returns:
        Tuple of (audio_data, sample_rate)
    """
    try:
        y, sr = librosa.load(file_path, sr=sr)
        return y, sr
    except Exception as e:
        logger.error(f"Failed to load audio: {e}")
        raise AudioProcessingError(f"Cannot load audio file: {e}")
```

### Song Structure Segmentation
- Use onset detection and novelty functions for section boundary detection
- Apply spectral clustering or similarity matrix analysis
- Implement confidence scoring for detected sections
- Allow for overlapping or uncertain section boundaries

### Key Detection
- Use chroma feature analysis with key templates
- Implement Krumhansl-Schmuckler key-finding algorithm
- Provide confidence scores for key detection
- Handle modulations and key changes within songs

### Tempo and Beat Analysis
- Use librosa's tempo estimation with multiple methods
- Implement beat tracking with confidence intervals
- Handle complex time signatures and tempo changes
- Provide beats-per-minute and beat positions

## Error Handling Patterns

### Audio Processing Errors
```python
class AudioProcessingError(Exception):
    """Raised when audio processing fails."""
    pass

class UnsupportedFormatError(AudioProcessingError):
    """Raised for unsupported audio formats."""
    pass

# Usage in analysis functions
try:
    result = analyze_audio_file(file_path)
except UnsupportedFormatError:
    return jsonify({"error": "Unsupported audio format"}), 400
except AudioProcessingError as e:
    logger.error(f"Analysis failed: {e}")
    return jsonify({"error": "Audio analysis failed"}), 500
```

### Memory Management
- Monitor memory usage for large audio files
- Implement streaming analysis when possible
- Clean up numpy arrays and temporary files
- Use context managers for file operations

## Testing Standards

### Unit Tests
- Test individual audio analysis functions with known audio samples
- Include edge cases: silence, noise, very short clips
- Test error handling with corrupted files
- Verify mathematical correctness of analysis algorithms

### Integration Tests
- Test complete API endpoints with real audio files
- Verify JSON response structure and content
- Test file upload functionality
- Test concurrent analysis requests

### Performance Tests
- Test analysis speed with various file sizes
- Monitor memory usage during analysis
- Test with files of different durations (10 seconds to 10 minutes)
- Verify timeout handling for very long files

## Logging and Monitoring

### Structured Logging
```python
import logging

# Configure logging for audio analysis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log analysis progress
logger.info(f"Starting analysis for file: {filename}")
logger.info(f"Detected {len(sections)} sections in {duration:.2f} seconds")
```

### Performance Metrics
- Track analysis duration for different file types and sizes
- Monitor memory peak usage during processing
- Log successful vs failed analysis attempts
- Track API response times

## Advanced Analysis Features

### Harmonic Analysis
- Implement pitch class profiles for key detection
- Use harmonic change detection for section boundaries
- Apply chord recognition algorithms with confidence scoring
- Handle complex harmonies and extended chords

### Rhythmic Analysis
- Detect time signature changes
- Analyze rhythmic complexity and patterns
- Implement groove analysis for different musical styles
- Detect tempo variations and rubato

### Spectral Analysis
- Use mel-frequency cepstral coefficients (MFCC) for timbre analysis
- Implement spectral centroid and rolloff for brightness detection
- Apply zero-crossing rate for texture analysis
- Use spectral contrast for harmonic vs percussive separation

## Configuration Management

### Environment Variables
```python
import os

# Configuration with sensible defaults
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', tempfile.gettempdir())
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 100 * 1024 * 1024))  # 100MB
ANALYSIS_TIMEOUT = int(os.getenv('ANALYSIS_TIMEOUT', 300))  # 5 minutes
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
```

### Analysis Parameters
- Make audio analysis parameters configurable
- Provide different analysis quality/speed trade-offs
- Allow customization of section detection sensitivity
- Support different musical styles and genres

## Security Considerations

### File Upload Security
- Validate file extensions and magic numbers
- Limit file sizes and analysis duration
- Use secure temporary file handling
- Sanitize all user inputs

### API Security
- Implement rate limiting for analysis requests
- Validate all request parameters
- Use proper CORS configuration for local development
- Log security-relevant events

## Deployment Considerations

### Production Settings
- Configure appropriate logging levels
- Set resource limits for memory and CPU usage
- Implement health check endpoints
- Use proper error handling middleware

### Docker Support
- Create Dockerfile with audio processing dependencies
- Handle audio codec installation in containers
- Configure proper volume mounts for temporary files
- Set appropriate container resource limits