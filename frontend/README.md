# Sectionist Python Frontend

This is the cross-platform Python frontend for Sectionist. It works on Windows, macOS, and Linux.

## Features

- ✅ **Cross-platform compatibility** (Windows, macOS, Linux)
- ✅ **Drag & drop audio file support**
- ✅ **Communication with existing Python backend**
- ✅ **Audio playback controls**
- ✅ **Timeline visualization with clickable sections**
- ✅ **Analysis results display**
- ✅ **Professional native-looking interface**

## Technology Stack

- **GUI Framework**: PyQt6 (native widgets, cross-platform)
- **Audio Playback**: python-vlc (requires the VLC media player / libvlc library)
- **Backend Communication**: requests (reuses the HTTP API)
- **Audio Metadata**: mutagen (file information)

## Quick Start

### Prerequisites

- Python 3.8+
- VLC media player installed (provides the `libvlc` library used by python-vlc)
- Backend server running (see `../backend/start_server.sh`)

### Installation

1. **Set up the Python frontend**:
   ```bash
   cd frontend
   ./setup.sh
   ```

2. **Start the backend server** (in another terminal):
   ```bash
   cd backend
   ./start_server.sh
   ```

3. **Run the Python frontend**:
   ```bash
   cd frontend
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

## Limitations and Future Work

### Current Limitations
- ⚠️ Audio playback requires the VLC media player (libvlc) to be installed
- ⚠️ No drag-to-rearrange sections yet
- ⚠️ No section editing UI yet

### Future Enhancements
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

1. `sectionist_gui.py` is the entry point; the main window lives in `main_window.py`
2. Timeline drawing lives in `timeline_widget.py`
3. Audio playback is handled by `audio_player.py` (python-vlc)
4. `analysis_worker.py` handles backend communication
5. Add new widgets by subclassing PyQt6 widgets
6. Follow PyQt6 best practices for threading and signals

## Troubleshooting

### "PyQt6 not found"
```bash
pip install PyQt6
```

### "Cannot connect to backend server"
- Make sure the backend is running on port 8765
- Check that `http://127.0.0.1:8765/health` returns a response

### Audio playback issues
- Make sure the VLC media player is installed so `libvlc` is available to python-vlc
- On Linux, install the `libvlc5` and `libvlccore9` packages
- Check that your audio file is in a supported format

### Linux-specific issues
- Install system audio libraries: `sudo apt-get install libasound2-dev`
- For PyQt6: `sudo apt-get install python3-pyqt6`
- For playback: `sudo apt-get install libvlc5 libvlccore9`

This Python frontend provides cross-platform audio analysis with the same core functionality on Windows, macOS, and Linux.