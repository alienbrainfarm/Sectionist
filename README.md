# Sectionist

Sectionist is a macOS application that helps musicians analyze songs by splitting audio into meaningful sections (intro, verse, chorus, etc.), detecting key changes, and mapping basic chords. The app uses a SwiftUI frontend and a local Python backend for audio/ML processing.

**Current Features:**
- 📄 Comprehensive development documentation
- 🏗️ Project structure and architecture planning
- 🎵 **Song structure segmentation (intro, verse, chorus, etc.)**
- 🎹 **Key and tempo detection**  
- 📡 **SwiftUI ↔ Python HTTP communication**
- 🎸 Basic chord mapping (backend ready, UI pending)

**Planned Features:**
- 🎵 Song structure segmentation (intro, verse, chorus, etc.)
- 🎹 Key and key change detection  
- 🎸 Basic chord mapping
- 🎤 (Future) Lyric extraction from audio

## Tech Stack

- **Frontend:** Swift/SwiftUI (macOS app)
- **Backend:** Python (audio processing & ML inference)
- **Audio Analysis:** librosa, numpy, scipy
- **Communication:** Local HTTP API or IPC

## Quick Start

### Prerequisites

- macOS 12.0+ (required for SwiftUI)
- Xcode 14+ with command line tools
- Python 3.8+
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/alienbrainfarm/Sectionist.git
   cd Sectionist
   ```

2. **Set up the backend:**
   ```bash
   cd backend
   ./start_server.sh
   ```
   
   The startup script will:
   - Create a Python virtual environment
   - Install all required dependencies (librosa, flask, etc.)
   - Start the HTTP server on `http://127.0.0.1:5000`

3. **Set up the frontend:**
   ```bash
   cd ../Sectionist
   open Sectionist.xcodeproj
   # Build and run in Xcode (⌘+R)
   ```

### Usage

1. **Start the backend server** (if not already running):
   ```bash
   cd backend && ./start_server.sh
   ```

2. **Launch the SwiftUI app** from Xcode

3. **Analyze audio files**:
   - Drag and drop an audio file into the app, or
   - Click "Choose File" to select an audio file
   - Click "Analyze Audio" to process the file
   - View the results in the timeline and analysis panels

### Development Setup

For detailed development setup instructions, see [CONTRIBUTING.md](CONTRIBUTING.md).

**Quick development setup:**
```bash
# Backend development
cd backend/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install black flake8 pytest mypy  # Dev dependencies

# Run backend (when implemented)
python src/main.py

# Frontend development  
cd Sectionist/
open Sectionist.xcodeproj
# Build and run in Xcode
```

## Project Structure

```
Sectionist/
├── README.md                 # This file
├── CONTRIBUTING.md          # Contribution guidelines
├── docs/
│   ├── PRD.md              # Product Requirements Document
│   └── DEVELOPMENT.md      # Development guide (planned)
├── Sectionist/             # SwiftUI macOS app (planned)
│   ├── Sectionist.xcodeproj
│   ├── Sources/
│   └── Tests/
├── backend/                # Python backend (planned)
│   ├── requirements.txt
│   ├── src/
│   │   ├── audio_analysis/
│   │   ├── segmentation/
│   │   ├── chord_detection/
│   │   └── api/
│   └── tests/
└── scripts/               # Build and utility scripts (planned)
```

## Development Workflow

This project follows a structured development workflow:

1. **Issues First** - All changes should start with a GitHub issue
2. **Feature Branches** - Use `feature/issue-name` or `bugfix/issue-name` 
3. **Pull Requests** - All changes go through PR review
4. **Testing** - Include tests for new functionality
5. **Documentation** - Update docs for user-facing changes

See [CONTRIBUTING.md](CONTRIBUTING.md) for complete guidelines.

## Roadmap

### Phase 1: Foundation (Current)
- [x] Project setup and documentation
- [x] Basic project structure (Swift + Python)
- [x] Development environment setup
- [x] **Frontend-backend communication via HTTP API**
- [ ] CI/CD pipeline

### Phase 2: Core Audio Analysis  
- [x] Audio file loading and preprocessing
- [x] Basic song segmentation algorithm
- [x] Key detection implementation
- [x] **Frontend-backend communication**

### Phase 3: User Interface
- [ ] SwiftUI audio timeline visualization
- [ ] Drag-and-drop audio file support
- [ ] Section labeling and editing
- [ ] Results export functionality

### Phase 4: Advanced Features
- [ ] Chord detection and mapping
- [ ] Key change detection
- [ ] Improved segmentation accuracy
- [ ] Performance optimization

### Future Enhancements
- [ ] Lyric extraction from audio
- [ ] Export to music notation software
- [ ] Batch processing capabilities
- [ ] Plugin architecture

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development setup instructions
- Code style guidelines  
- Pull request process
- Testing requirements
- Issue reporting guidelines

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes with tests
4. Run linting and tests
5. Submit a pull request

## Documentation

- **[Product Requirements](docs/PRD.md)** - Detailed product specification
- **[Contributing Guide](CONTRIBUTING.md)** - Development and contribution guidelines
- **[Development Setup](docs/DEVELOPMENT.md)** - Detailed dev environment setup (planned)

## Technology Details

### Frontend (SwiftUI)
- Native macOS application
- Drag-and-drop file support
- Real-time audio visualization
- Timeline-based section editing

### Backend (Python)
- Audio processing with librosa
- Machine learning for section detection
- Local inference (no cloud dependencies)
- RESTful API for frontend communication

### Audio Analysis Pipeline
1. **Preprocessing** - Audio normalization and feature extraction
2. **Segmentation** - Identify song sections using ML models
3. **Key Detection** - Analyze harmonic content for key identification  
4. **Chord Analysis** - Map basic chord progressions
5. **Post-processing** - Clean up and validate results

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: General questions and community discussion
- **Documentation**: Check the `docs/` folder for detailed guides

---

**Status**: 🚧 Early Development - This project is in active development. The core functionality is built and working for local analysis.

## Communication Architecture

The application uses a local HTTP server architecture:

- **Frontend**: SwiftUI macOS app with drag-and-drop file support
- **Backend**: Python Flask server running locally (`http://127.0.0.1:5000`)
- **Communication**: REST API with JSON data exchange
- **Analysis**: librosa-based audio processing with music information retrieval

See [Communication Protocol Documentation](docs/COMMUNICATION_PROTOCOL.md) for detailed API specifications.

## Troubleshooting

### Backend Issues

1. **"librosa not available" error**:
   ```bash
   cd backend
   source venv/bin/activate
   pip install --force-reinstall librosa
   ```

2. **"Port already in use" error**:
   ```bash
   # Find and kill process using port 5000
   lsof -ti:5000 | xargs kill -9
   ```

3. **Python dependencies missing**:
   ```bash
   cd backend
   ./start_server.sh  # This will reinstall everything
   ```

### Frontend Issues

1. **"Connection refused" error in SwiftUI app**:
   - Make sure the backend server is running
   - Check that `http://127.0.0.1:5000/health` returns a response

2. **File access errors**:
   - Ensure the audio file is in a accessible location
   - Try copying the file to your Documents folder

3. **Build errors in Xcode**:
   - Make sure you have Xcode 14+ installed
   - Clean build folder (⌘+Shift+K) and rebuild

### Performance Issues

- Large files (>10 minutes) may take 2-3 minutes to process
- Supported formats: MP3, WAV, AIFF, M4A, FLAC, OGG, AAC
- Maximum file size: 100MB
