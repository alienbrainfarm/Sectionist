# Sectionist

![CI/CD Pipeline](https://github.com/alienbrainfarm/Sectionist/workflows/CI%2FCD%20Pipeline/badge.svg)
[![codecov](https://codecov.io/gh/alienbrainfarm/Sectionist/branch/main/graph/badge.svg)](https://codecov.io/gh/alienbrainfarm/Sectionist)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Sectionist is a macOS application that helps musicians analyze songs by splitting audio into meaningful sections (intro, verse, chorus, etc.), detecting key changes, and mapping basic chords. The app uses a SwiftUI frontend and a local Python backend for audio/ML processing.

**Current Features:**
- 📄 Comprehensive development documentation
- 🏗️ Complete project structure and architecture
- 🎵 **Song structure segmentation (intro, verse, chorus, etc.)**
- 🎹 **Key and tempo detection**  
- 📡 **SwiftUI ↔ Python HTTP communication**
- 🖥️ **Native macOS SwiftUI frontend with drag-and-drop support**
- 🐍 **Python Flask backend with librosa-based audio analysis**
- 📊 **Timeline visualization and analysis results display**
- ✏️ **Section labeling and editing UI** ⭐ **NEW**
- 🎸 Basic chord mapping (backend implemented, frontend integration in progress)

**Planned Features:**
- 🎸 Enhanced chord mapping UI and visualization
- 📁 Export functionality (PDF, text, MIDI)
- 🎤 Lyric extraction from audio
- 🔄 Batch processing capabilities

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
├── LICENSE                   # MIT License
├── CONTRIBUTING.md          # Contribution guidelines
├── docs/
│   ├── PRD.md              # Product Requirements Document
│   ├── DEVELOPMENT.md      # Development guide
│   ├── CI_CD.md            # CI/CD pipeline documentation
│   └── COMMUNICATION_PROTOCOL.md  # API specifications
├── Sectionist/             # SwiftUI macOS app ✅ IMPLEMENTED
│   ├── Sectionist.xcodeproj
│   ├── SectionistApp.swift      # App entry point
│   ├── ContentView.swift        # Main UI
│   ├── AnalysisService.swift    # Backend communication
│   ├── AnalysisResultsView.swift # Results display
│   ├── TimelineView.swift       # Timeline visualization
│   └── Assets.xcassets
├── backend/                # Python backend ✅ IMPLEMENTED
│   ├── requirements.txt    # Production dependencies
│   ├── requirements-dev.txt # Development dependencies
│   ├── server.py          # Flask HTTP server
│   ├── example.py         # Core analysis algorithms
│   ├── start_server.sh    # Server startup script
│   └── test_*.py          # Test suite
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

### Phase 1: Foundation ✅ **COMPLETED**
- [x] Project setup and documentation
- [x] Basic project structure (Swift + Python)
- [x] Development environment setup
- [x] **Frontend-backend communication via HTTP API**
- [x] **CI/CD pipeline with comprehensive testing and quality assurance**

### Phase 2: Core Audio Analysis ✅ **COMPLETED**
- [x] Audio file loading and preprocessing
- [x] Basic song segmentation algorithm
- [x] Key detection implementation
- [x] **Frontend-backend HTTP communication**
- [x] **SwiftUI timeline visualization foundation**

### Phase 3: User Interface ✅ **COMPLETED**
- [x] SwiftUI audio timeline visualization (basic implementation)
- [x] Drag-and-drop audio file support
- [x] Section labeling and editing UI
- [ ] Results export functionality

### Phase 4: Advanced Features
- [x] Core chord detection algorithm (backend)
- [ ] Chord mapping UI integration
- [ ] Key change detection visualization
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
- **[Development Setup](docs/DEVELOPMENT.md)** - Detailed dev environment setup
- **[CI/CD Pipeline](docs/CI_CD.md)** - Continuous integration and deployment guide
- **[Section Editing UI](docs/SECTION_EDITING_UI.md)** - Manual section editing and labeling features

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

**Status**: 🚀 **Active Development** - Core functionality is implemented and working. The SwiftUI frontend communicates with the Python backend via HTTP API for real-time audio analysis. Currently polishing UI and adding advanced features.

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
