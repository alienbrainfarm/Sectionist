# Sectionist - GitHub Copilot Instructions

## Project Overview

Sectionist is a cross-platform audio analysis application that helps musicians analyze songs by splitting audio into meaningful sections (intro, verse, chorus, etc.), detecting key changes, and mapping basic chords. The application uses a Python backend with librosa for audio processing and a Python frontend with PyQt6 for cross-platform GUI compatibility.

## Architecture

- **Backend**: Python Flask HTTP server with librosa-based audio analysis
- **Frontend**: Python PyQt6 cross-platform GUI application
- **Communication**: Local HTTP API (JSON REST endpoints)
- **Platforms**: Windows, macOS, Linux
- **Audio Processing**: librosa, numpy, scipy for music information retrieval

## Technology Stack

### Backend Dependencies
- `librosa>=0.10.0` - Core audio analysis and feature extraction
- `numpy>=1.24.0` - Numerical computations
- `scipy>=1.10.0` - Scientific computing
- `flask>=2.3.0` - Web framework for REST API
- `pytest>=7.0.0` - Testing framework

### Frontend Dependencies
- `PyQt6>=6.5.0` - Cross-platform GUI framework
- `python-vlc>=3.0.0` - Audio playback
- `requests>=2.31.0` - HTTP communication with backend
- `mutagen>=1.47.0` - Audio file metadata
- `pytest>=7.0.0` - Testing framework

## Coding Standards

### General Python Guidelines
- Follow **PEP 8** style guide strictly
- Use type hints for all function parameters and return values
- Include comprehensive docstrings following **PEP 257** conventions
- Maintain line length of 79 characters maximum
- Use 4 spaces for indentation
- Write clear, descriptive variable and function names

### Audio Processing Code
- Always handle audio file format compatibility (MP3, WAV, AIFF, M4A, FLAC, OGG, AAC)
- Include proper error handling for corrupted or unsupported audio files
- Use librosa's built-in functions for feature extraction (MFCC, spectrograms, tempo, key)
- Implement proper memory management for large audio files
- Include progress callbacks for long-running analysis operations
- Document audio analysis algorithms with clear explanations of the approach

### Backend API Design
- Follow REST conventions for endpoint design
- Use Flask's request validation and error handling
- Implement proper HTTP status codes (200, 400, 404, 500)
- Include comprehensive logging for debugging audio analysis issues
- Validate file uploads with size limits and allowed extensions
- Use secure filename handling for uploaded files

### Frontend GUI Development
- Follow PyQt6 best practices and Qt design patterns
- Implement proper threading for long-running operations (use QThread)
- Use proper signal/slot connections for UI updates
- Implement drag-and-drop functionality consistently
- Ensure cross-platform compatibility (test on Windows, macOS, Linux)
- Include proper audio playback controls with seeking and position tracking
- Implement timeline visualization with interactive editing capabilities

### File Structure Guidelines

#### Backend Structure (`backend/`)
- `server.py` - Flask HTTP server and API endpoints
- `example.py` - Core audio analysis algorithms
- `test_*.py` - Test files for backend functionality
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies (if needed)

#### Frontend Structure (`frontend/`)
- `sectionist_gui.py` - Main application entry point
- `main_window.py` - Main window UI logic and layout
- `timeline_widget.py` - Timeline visualization and editing
- `audio_player.py` - VLC-based audio playback functionality
- `analysis_worker.py` - Background analysis communication
- `test_*.py` - Test files for frontend functionality
- `requirements.txt` - Frontend dependencies

## Testing Standards

### Test Organization
- Use pytest for all testing
- Include unit tests for audio analysis algorithms
- Include integration tests for API endpoints
- Include GUI tests for user interface components
- Test cross-platform compatibility where possible

### Audio Testing
- Include test audio files in common formats for testing
- Test edge cases: empty files, corrupted files, very short/long files
- Test performance with large audio files (>10 minutes)
- Include regression tests for analysis accuracy

### API Testing
- Test all HTTP endpoints with valid and invalid inputs
- Test file upload functionality with various file types
- Test error handling and appropriate HTTP status codes
- Include performance tests for analysis endpoints

## Error Handling

### Audio Processing Errors
- Handle librosa exceptions gracefully with user-friendly messages
- Provide specific error messages for unsupported audio formats
- Include fallback analysis methods for edge cases
- Log detailed error information for debugging

### GUI Error Handling
- Display user-friendly error dialogs for analysis failures
- Implement proper exception handling in Qt event handlers
- Provide progress indicators for long-running operations
- Handle backend communication failures gracefully

## Performance Considerations

### Audio Analysis
- Implement streaming analysis for large files when possible
- Use efficient numpy operations for signal processing
- Cache intermediate analysis results when appropriate
- Optimize memory usage for batch processing

### GUI Responsiveness
- Always run audio analysis in background threads
- Update UI progressively during analysis
- Implement proper cancellation for long-running operations
- Use efficient Qt models for timeline data visualization

## Security Considerations

### File Handling
- Validate all uploaded audio files
- Use secure temporary file handling
- Limit file sizes (default: 100MB maximum)
- Sanitize filenames to prevent path traversal attacks

### API Security
- Validate all input parameters
- Implement rate limiting for analysis endpoints
- Use proper CORS headers for local development
- Log security-relevant events

## Documentation Standards

### Code Documentation
- Include module-level docstrings explaining purpose and usage
- Document all public functions with parameters, return values, and examples
- Include inline comments for complex audio processing algorithms
- Provide usage examples for API endpoints

### User Documentation
- Update README.md with setup and usage instructions
- Include troubleshooting guides for common issues
- Document audio format support and limitations
- Provide development setup instructions

## Development Workflow

### Branch Management
- Use feature branches for new functionality
- Follow naming convention: `feature/issue-description` or `bugfix/issue-description`
- Include tests with all code changes
- Update documentation for user-facing changes

### Code Review Guidelines
- Review audio analysis algorithms for accuracy and efficiency
- Verify cross-platform compatibility for GUI changes
- Check error handling and edge case coverage
- Ensure proper testing coverage for new features

## Audio Analysis Best Practices

### Librosa Usage
- Use appropriate hop lengths for time-based analysis
- Apply proper windowing for frequency analysis
- Handle stereo vs mono audio consistently
- Use appropriate sample rates (typically 22050 Hz for analysis)

### Music Information Retrieval
- Implement robust onset detection for section boundaries
- Use harmonic analysis for key detection
- Apply tempo estimation with confidence scoring
- Implement chord recognition with probability estimates

### Timeline Visualization
- Provide sample-accurate timeline positioning
- Implement zoom and scroll functionality
- Use consistent color coding for different analysis results
- Allow user editing of detected sections

## Common Patterns

### Background Processing
```python
# Use QThread for long-running operations
class AnalysisWorker(QThread):
    progress_updated = pyqtSignal(int)
    analysis_completed = pyqtSignal(dict)
    
    def run(self):
        # Implement analysis with progress updates
        pass
```

### API Communication
```python
# Consistent error handling for API calls
try:
    response = requests.post(url, files=files, timeout=30)
    response.raise_for_status()
    return response.json()
except requests.exceptions.RequestException as e:
    # Handle and log errors appropriately
    logger.error(f"API request failed: {e}")
    raise
```

### Audio File Handling
```python
# Consistent audio file loading with error handling
def load_audio_file(file_path: str) -> Tuple[np.ndarray, int]:
    """Load audio file with librosa and handle common errors."""
    try:
        y, sr = librosa.load(file_path, sr=None)
        return y, sr
    except Exception as e:
        logger.error(f"Failed to load audio file {file_path}: {e}")
        raise AudioLoadError(f"Cannot load audio file: {e}")
```

## Implementation Notes

- The application previously had a Swift/SwiftUI frontend that has been archived
- Focus on maintaining compatibility with the existing backend API
- Prioritize cross-platform functionality over platform-specific features
- Implement progressive enhancement for advanced audio analysis features
- Consider memory usage for large audio files and long analysis sessions