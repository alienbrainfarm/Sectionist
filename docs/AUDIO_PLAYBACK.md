# Audio Playback Feature

## Overview

The Sectionist app now includes full audio playback functionality that allows users to play and listen to their audio files directly within the application. This feature integrates seamlessly with the existing timeline visualization and section analysis.

## Features

### ✅ Implemented Features

- **Play/Pause Control**: Click the prominent play/pause button to start or stop audio playback
- **Timeline Synchronization**: The timeline position updates in real-time during playback
- **Section Seeking**: Click on any song section in the timeline to jump directly to that part of the audio
- **Skip Controls**: Skip backward or forward by 10 seconds using the dedicated skip buttons
- **Playback Speed**: Adjust playback speed from 0.5x to 2x using the speed control menu
- **Progress Scrubbing**: Drag the timeline slider to seek to any position in the audio
- **Audio Format Support**: Supports all major audio formats (MP3, WAV, M4A, FLAC, AAC, etc.)
- **Error Handling**: Clear error messages for file access issues or playback problems

### 🎯 Key Components

#### AudioPlayerService.swift
- **Purpose**: Core audio playback service using AVFoundation
- **Key Methods**:
  - `loadAudio(from:)` - Load an audio file for playback
  - `togglePlayback()` - Play/pause toggle
  - `seek(to:)` - Seek to specific time position
  - `skipBackward/skipForward()` - Skip by specified seconds
  - `setPlaybackRate()` - Adjust playback speed

#### Enhanced Timeline Integration
- **Real-time Updates**: Timeline position reflects actual playback position
- **Section Integration**: Clicking sections seeks to that audio position
- **Visual Feedback**: Play button state reflects actual playback status

## Usage Instructions

### Basic Playbook
1. **Load Audio File**: Drag and drop or select an audio file using "Choose File"
2. **Analyze (Optional)**: Click "Analyze Audio" to detect song sections
3. **Play Audio**: Click the large play button (▶️) in the timeline controls
4. **Control Playback**:
   - **Pause**: Click the pause button (⏸️) 
   - **Seek**: Drag the timeline slider or click on song sections
   - **Skip**: Use the 10-second skip buttons (⏪ ⏩)
   - **Speed**: Use the speed menu to adjust playback rate

### Advanced Features
- **Section Navigation**: Click any colored section block to jump to that part of the song
- **Precise Seeking**: Drag the timeline slider for frame-accurate positioning
- **Speed Control**: Useful for detailed analysis - slow down to 0.5x or speed up to 2x
- **Error Recovery**: Clear error messages help troubleshoot file access or playback issues

## Technical Implementation

### Audio Session Management
- Configures macOS audio session for optimal playback
- Handles security-scoped resource access for sandboxed environment
- Proper cleanup when switching between files

### Performance Considerations
- Efficient timer-based position updates (0.1s intervals during playback)
- Minimal CPU usage when not playing
- Proper memory management and resource cleanup

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
- Playbook continues to work while editing sections
- Seeking to edited sections works as expected
- Real-time feedback helps verify section boundaries

## Browser/Platform Support

- **Platforms**: macOS 12.0+ (native AVFoundation integration)
- **Audio Formats**: MP3, WAV, AIFF, M4A, FLAC, OGG, AAC, WMA, OPUS
- **File Size**: Up to 100MB (configurable)
- **Performance**: Optimized for files up to 10 minutes duration

## Troubleshooting

### Common Issues
1. **"Cannot access audio file"**
   - Ensure file is in an accessible location (not in restricted folders)
   - Try copying the file to Documents folder

2. **"Failed to load audio"**
   - Check that the file format is supported
   - Verify the file is not corrupted
   - Try with a different audio file

3. **Playback stutters or stops**
   - Check available system memory
   - Close other audio applications
   - Try reducing playback speed

### Debug Information
- Error messages appear below the playback controls
- Check Console.app for detailed error logging
- Audio player service provides comprehensive error descriptions

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

### AudioPlayerService Methods

```swift
// Load audio file
audioPlayer.loadAudio(from: audioFileURL)

// Control playback
audioPlayer.play()
audioPlayer.pause()
audioPlayer.togglePlayback()
audioPlayer.stop()

// Navigation
audioPlayer.seek(to: timeInSeconds)
audioPlayer.skipBackward(seconds: 10)
audioPlayer.skipForward(seconds: 10)

// Configuration
audioPlayer.setPlaybackRate(1.5) // 1.5x speed
```

### Observable Properties

```swift
@Published var isPlaying: Bool           // Current playback state
@Published var currentTime: TimeInterval // Current position in seconds
@Published var duration: TimeInterval    // Total audio duration
@Published var playbackRate: Float       // Current playback rate
@Published var errorMessage: String?     // Error message if any
```

This implementation provides a complete audio playbook solution that enhances the music analysis workflow by allowing users to immediately verify their analysis results against the actual audio content.