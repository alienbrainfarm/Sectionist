# Audio Playback Feature

## Overview

The Sectionist app includes audio playback functionality that allows users to play and listen to their audio files directly within the application. This feature integrates seamlessly with the existing timeline visualization and section analysis.

## Features

### ✅ Implemented Features

- **Play/Pause Control**: Click the play/pause button to start, pause, or resume audio playback
- **Timeline Synchronization**: The timeline position updates in real-time during playback
- **Section Seeking**: Click on any song section in the timeline to jump directly to that part of the audio
- **Stop Control**: Stop playback and reset the position to the start
- **Progress Scrubbing**: Drag the position slider to seek to any position in the audio
- **Audio Format Support**: Supports all major audio formats (MP3, WAV, M4A, FLAC, AAC, etc.)
- **Error Handling**: Clear error messages for file access issues or playback problems

### 🎯 Key Components

#### `frontend/audio_player.py`
- **Purpose**: Core audio playback wrapper around **python-vlc** (requires the VLC media player / libvlc library)
- **Key Methods**:
  - `load_file(file_path)` - Load an audio file for playback
  - `play()` / `pause()` / `stop()` - Control playback
  - `set_position(seconds)` - Seek to a specific time position
  - `get_position()` - Read the current position in seconds
  - `get_duration()` - Read the total audio duration

#### Enhanced Timeline Integration
- **Real-time Updates**: Timeline position reflects actual playback position
- **Section Integration**: Clicking sections seeks to that audio position
- **Visual Feedback**: Play button state reflects actual playback status
- **State Polling**: A `QTimer` in `main_window.py` polls the player every 100ms while playing

## Usage Instructions

### Basic Playback
1. **Load Audio File**: Drag and drop or select an audio file using "Choose File"
2. **Analyze (Optional)**: Click "Analyze Audio" to detect song sections
3. **Play Audio**: Click the large play button (▶️) in the timeline controls
4. **Control Playback**:
   - **Pause**: Click the pause button (⏸️)
   - **Stop**: Click the stop button (⏹) to stop and reset
   - **Seek**: Drag the position slider or click on song sections

### Advanced Features
- **Section Navigation**: Click any colored section block to jump to that part of the song
- **Precise Seeking**: Drag the position slider for precise positioning
- **Error Recovery**: Clear error messages help troubleshoot file access or playback issues

## Technical Implementation

### Audio Player Module
- Wraps **python-vlc**, which loads the **VLC media player** system library (`libvlc`)
- VLC is initialised lazily on first file load, so importing the module does not require a working libvlc installation
- Duration is read from VLC, with mutagen used as a fallback
- Playback state and position are polled from VLC by a `QTimer` in `main_window.py`

### Seeking
- VLC represents positions as a ratio between `0.0` and `1.0`
- `audio_player.set_position(seconds)` converts seconds to a ratio before seeking
- `audio_player.get_position()` converts the VLC ratio back to seconds

### Performance Considerations
- Efficient timer-based position updates (100ms intervals during playback)
- Timer stops when playback is paused or stopped, keeping CPU usage low
- Proper cleanup when switching between files

### Error Handling
- File access validation
- Audio format compatibility checking
- Clear user feedback for all error conditions
- Graceful degradation when audio fails to load

## Integration with Existing Features

### Analysis Results
- Audio playback works independently of analysis results
- Can play audio before, during, or after analysis
- Timeline shows both analysis results and playback position

### Section Editing
- Playback continues to work while editing sections
- Seeking to edited sections works as expected
- Real-time feedback helps verify section boundaries

## Platform Support

- **Platforms**: Windows, macOS, Linux
- **Audio Backend**: python-vlc (VLC media player / libvlc)
- **Audio Formats**: MP3, WAV, AIFF, M4A, FLAC, OGG, AAC, WMA, OPUS
- **File Size**: Up to 100MB (configurable)
- **Performance**: Optimized for files up to 10 minutes duration

## Troubleshooting

### Common Issues
1. **"Cannot access audio file"**
   - Ensure file is in an accessible location (not in restricted folders)
   - Try copying the file to the Documents folder

2. **"Failed to load audio"**
   - Check that the file format is supported
   - Verify the file is not corrupted
   - Try with a different audio file

3. **Playback stutters or stops**
   - Check available system memory
   - Close other audio applications
   - Confirm the VLC media player (libvlc) is installed and on the library path

### Debug Information
- Error messages appear below the playback controls
- Check the terminal running the frontend for python-vlc error output
- The audio player reports failures when loading or playing a file

## Future Enhancements

### Planned Features
- **Waveform Visualization**: Visual waveform display synchronized with playback
- **Loop Playback**: Loop individual sections for practice
- **Bookmark System**: Save and recall specific playback positions
- **Export Audio Clips**: Extract and save audio segments

### Performance Improvements
- **Background Loading**: Pre-load audio while analysis runs
- **Caching**: Cache decoded audio for faster seeking
- **Streaming**: Support for larger audio files via streaming playback

## API Reference

### AudioPlayer Methods

```python
# Load audio file
audio_player.load_file(file_path)

# Control playback
audio_player.play()
audio_player.pause()
audio_player.stop()

# Navigation
audio_player.set_position(time_in_seconds)
audio_player.get_position()

# Metadata
audio_player.get_duration()
```

### Playback State

```python
audio_player.is_playing   # Current playback state
audio_player.is_paused    # Whether playback is paused
audio_player.current_file # Path to the loaded audio file
audio_player.duration     # Total audio duration in seconds
```

This implementation provides a complete audio playback solution that enhances the music analysis workflow by allowing users to immediately verify their analysis results against the actual audio content.
