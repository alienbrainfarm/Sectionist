# Sectionist

Sectionist is a macOS application that helps musicians analyze songs by splitting audio into meaningful sections (intro, verse, chorus, etc.), detecting key changes, and mapping basic chords. The app uses a SwiftUI frontend and a local Python backend for audio/ML processing.

**Current Features:**
- 📄 Comprehensive development documentation
- 🏗️ Project structure and architecture planning

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

2. **Set up the backend** (when available):
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend** (when available):
   ```bash
   cd Sectionist
   open Sectionist.xcodeproj
   # Build and run in Xcode (⌘+R)
   ```

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
- [ ] Basic project structure (Swift + Python)
- [ ] Development environment setup
- [ ] CI/CD pipeline

### Phase 2: Core Audio Analysis  
- [ ] Audio file loading and preprocessing
- [ ] Basic song segmentation algorithm
- [ ] Key detection implementation
- [ ] Frontend-backend communication

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

**Status**: 🚧 Early Development - This project is in active development. The core functionality is being built and APIs may change.
