# Sectionist Backend

This is the Python backend for Sectionist, responsible for audio analysis, music information retrieval (MIR), and machine learning processing to detect song sections, keys, and chords.

## Features

- **Song Section Detection**: Automatically segment audio into sections (intro, verse, chorus, etc.)
- **Key Detection**: Identify the musical key and key changes
- **Chord Mapping**: Basic chord detection and mapping
- **Local Processing**: All analysis happens locally, no cloud uploads required

## Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Activate the virtual environment**:
   ```bash
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   # venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Verification

To verify the setup is working correctly, run the example script:

```bash
python example.py
```

This should display usage instructions. To test with an actual audio file:

```bash
python example.py /path/to/your/audio/file.mp3
```

## Usage

### Basic Audio Analysis

The `example.py` script demonstrates the core functionality:

```python
from example import analyze_audio_file

# Analyze an audio file
results = analyze_audio_file("song.mp3")
print(results)
```

### Expected Output Format

The analysis returns a dictionary with the following structure:

```json
{
    "file_path": "/path/to/song.mp3",
    "duration": 180.5,
    "tempo": 120.0,
    "key": "C major",
    "sections": [
        {"name": "Intro", "start": 0.0, "end": 45.0},
        {"name": "Verse", "start": 45.0, "end": 90.0},
        {"name": "Chorus", "start": 90.0, "end": 135.0},
        {"name": "Outro", "start": 135.0, "end": 180.5}
    ],
    "beats_detected": 360
}
```

## Dependencies

- **librosa**: Audio analysis and feature extraction
- **numpy**: Numerical computing
- **scipy**: Scientific computing
- **flask**: Web framework for API endpoints
- **pytest**: Testing framework

## Development

### Running Tests

```bash
pytest
```

### Adding New Features

1. Create feature modules in the backend directory
2. Add corresponding tests
3. Update requirements.txt if new dependencies are needed
4. Update this README with usage examples

### API Development

The backend is designed to work with the SwiftUI frontend through a REST API. Future development will include Flask endpoints for:

- `/analyze` - Analyze uploaded audio files
- `/status` - Check analysis status
- `/results/<job_id>` - Retrieve analysis results

## Supported Audio Formats

- MP3
- WAV
- AIFF
- FLAC
- M4A/AAC

## Performance Notes

- Processing time depends on audio length and complexity
- Typical processing: 30-60 seconds for a 4-minute song
- Memory usage: ~100-500MB during analysis

## Troubleshooting

### Common Issues

1. **"librosa not available" error**:
   - Make sure you've activated the virtual environment
   - Run `pip install -r requirements.txt`

2. **Audio file not found**:
   - Check the file path is correct
   - Ensure the file format is supported

3. **Performance issues**:
   - Large files (>10 minutes) may take longer to process
   - Consider downsampling for faster analysis if needed

### Getting Help

- Check the main project README for overall setup
- Review the PRD document in `docs/` for feature details
- Create an issue in the GitHub repository for bugs or feature requests

## Future Enhancements

- Advanced chord detection with extensions
- Real-time analysis capabilities  
- Export functionality (MIDI, PDF)
- Integration with external music software
- Lyric extraction using speech-to-text

## License

This project follows the same license as the main Sectionist project.