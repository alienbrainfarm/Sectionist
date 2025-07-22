# Sectionist Backend

This is the Python backend for Sectionist, responsible for audio analysis, music information retrieval (MIR), and machine learning processing to detect song sections, keys, and chords.

## Features

- **Song Section Detection**: Automatically segment audio into sections (intro, verse, chorus, etc.) using advanced Music Information Retrieval (MIR) techniques
- **Intelligent Boundary Detection**: Uses chroma features, energy analysis, and spectral characteristics to identify section changes
- **Confident Section Labeling**: Provides section labels with confidence scores based on musical characteristics and song position
- **Key Detection**: Identify the musical key and key changes
- **Chord Mapping**: Basic chord detection and mapping (planned)
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

### Testing the Segmentation

You can run the included test to validate the song structure segmentation:

```bash  
python test_segmentation.py
```

This creates synthetic test audio with known section boundaries and validates the algorithm's accuracy.

## Usage

### Basic Audio Analysis

The `example.py` script demonstrates the core song structure segmentation functionality:

```python
from example import analyze_audio_file

# Analyze an audio file
results = analyze_audio_file("song.mp3")

# Access segmentation results
print(f"Song duration: {results['duration']}s")
print(f"Detected {len(results['sections'])} sections:")
for section in results['sections']:
    print(f"  {section['name']}: {section['start']}s-{section['end']}s "
          f"(confidence: {section['confidence']})")
```

### Advanced Segmentation Features

The segmentation algorithm provides:
- **Intelligent boundary detection** using chroma, energy, and spectral analysis
- **Confident section labeling** with position-aware heuristics
- **Confidence scores** for each detected section (0.0-1.0)
- **Multiple section types**: Intro, Verse, Chorus, Bridge, Outro
- **Robustness** with fallback to basic sectioning for challenging audio

### Expected Output Format

The analysis returns a dictionary with the following structure:

```json
{
    "file_path": "/path/to/song.mp3",
    "duration": 180.5,
    "tempo": 120.0,
    "key": "C major",
    "sections": [
        {"name": "Intro", "start": 0.0, "end": 12.5, "confidence": 0.95},
        {"name": "Verse 1", "start": 12.5, "end": 32.0, "confidence": 0.87}, 
        {"name": "Chorus", "start": 32.0, "end": 52.5, "confidence": 0.92},
        {"name": "Bridge", "start": 52.5, "end": 68.0, "confidence": 0.76},
        {"name": "Outro", "start": 68.0, "end": 180.5, "confidence": 0.89}
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

The backend is designed to work with the Python frontend through a REST API. Current and future Flask endpoints include:

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