# Sectionist Python Frontend

This is a cross-platform Python frontend for Sectionist that replaces the Swift/SwiftUI version. It provides the same functionality but works on Windows, macOS, and Linux.

## Features

- ✅ **Cross-platform compatibility** (Windows, macOS, Linux)
- ✅ **Drag & drop audio file support**
- ✅ **Communication with existing Python backend**
- ✅ **Audio playback controls**
- ✅ **Timeline visualization with clickable sections**
- ✅ **Analysis results display**
- ✅ **Professional native-looking interface**
- ✅ **No Swift/Xcode dependency**

## Technology Stack

- **GUI Framework**: PyQt6 (native widgets, cross-platform)
- **Audio Playback**: pygame (simple, cross-platform)
- **Backend Communication**: requests (reuses existing HTTP API)
- **Audio Metadata**: mutagen (file information)

## Quick Start

### Prerequisites

- Python 3.8+
- Backend server running (see `../backend/start_server.sh`)

### Installation

1. **Set up the Python frontend**:
   ```bash
   cd frontend-python
   ./setup.sh
   ```

2. **Start the backend server** (in another terminal):
   ```bash
   cd backend
   ./start_server.sh
   ```

3. **Run the Python frontend**:
   ```bash
   cd frontend-python
   source venv/bin/activate
   python sectionist_gui.py
   ```

## Usage

1. **Load an audio file**:
   - Drag & drop an audio file into the application, or
   - Click "Browse..." to select a file

2. **Analyze the audio**:
   - Click "Analyze Audio" to process the file
   - Wait for the analysis to complete

3. **View results**:
   - See song sections in the timeline
   - View detailed analysis results
   - Use playback controls to listen to the audio

4. **Interactive features**:
   - Click on sections in the timeline to jump to that position
   - Use play/pause/stop controls
   - View chord progressions and key changes

## Supported Audio Formats

- MP3, WAV, AIFF, M4A, FLAC, OGG, AAC
- Same formats as the original Swift version

## Architecture

The Python frontend communicates with the existing Python backend via HTTP API:

```
┌─────────────────────┐    HTTP API    ┌─────────────────────┐
│   Python Frontend  │ ←──────────→   │   Python Backend   │
│   (PyQt6 GUI)      │                │   (Flask + librosa) │
└─────────────────────┘                └─────────────────────┘
```

This approach:
- ✅ Reuses the existing, working backend
- ✅ Maintains the same analysis quality
- ✅ Provides cross-platform compatibility
- ✅ Eliminates Swift/Xcode dependency

## Differences from Swift Version

### Advantages
- ✅ Cross-platform (Windows, macOS, Linux)
- ✅ Single language ecosystem (all Python)
- ✅ No Xcode dependency
- ✅ Easier deployment and distribution
- ✅ Better Windows 11 support

### Current Limitations
- ⚠️ Audio seeking is limited (pygame limitation)
- ⚠️ No drag-to-rearrange sections yet
- ⚠️ No section editing UI yet

### Future Enhancements
- 🔜 Advanced audio playback with seeking (using different audio library)
- 🔜 Section editing and manual adjustment
- 🔜 Enhanced timeline visualization
- 🔜 Export functionality
- 🔜 Drag-to-rearrange sections

## Development

### Running Tests
```bash
source venv/bin/activate
pytest
```

### Building for Distribution
```bash
# Install PyInstaller
pip install pyinstaller

# Build standalone executable
pyinstaller --onefile --windowed sectionist_gui.py
```

### Adding New Features

1. The main application is in `sectionist_gui.py`
2. Add new widgets by subclassing PyQt6 widgets
3. Use the existing `AnalysisWorker` for backend communication
4. Follow PyQt6 best practices for threading and signals

## Troubleshooting

### "PyQt6 not found"
```bash
pip install PyQt6
```

### "Cannot connect to backend server"
- Make sure the backend is running on port 5000
- Check that `http://127.0.0.1:5000/health` returns a response

### Audio playback issues
- Make sure pygame is installed: `pip install pygame`
- Check that your audio file is in a supported format

### Linux-specific issues
- Install system audio libraries: `sudo apt-get install libasound2-dev`
- For PyQt6: `sudo apt-get install python3-pyqt6`

## Comparison with Swift Version

| Feature | Swift Version | Python Version |
|---------|---------------|----------------|
| Platform Support | macOS only | Windows, macOS, Linux |
| Development Setup | Xcode required | Python + pip |
| Audio Playback | AVFoundation | pygame |
| GUI Framework | SwiftUI | PyQt6 |
| Backend Communication | HTTP API | HTTP API (same) |
| File Drag & Drop | ✅ | ✅ |
| Timeline Visualization | ✅ | ✅ |
| Section Editing | ✅ | 🔜 Planned |
| Audio Seeking | ✅ | ⚠️ Limited |
| Native Look & Feel | ✅ | ✅ |

## Migration Benefits

1. **Cross-Platform**: Works on Windows 11, solving the original issue
2. **Unified Ecosystem**: Everything is Python, easier maintenance
3. **No Platform Lock-in**: Not dependent on Apple's development tools
4. **Easier Distribution**: Python packages vs. macOS app bundles
5. **Community**: Larger Python GUI development community

This Python frontend provides a viable alternative to the Swift version while maintaining the same core functionality and improving cross-platform compatibility.