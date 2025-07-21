# Contributing to Sectionist

Thank you for your interest in contributing to Sectionist! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Setting Up Your Development Environment](#setting-up-your-development-environment)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Testing](#testing)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

By participating in this project, you agree to maintain a respectful, inclusive, and collaborative environment. Please be kind and constructive in all interactions.

## Getting Started

### Prerequisites

Before you start contributing, make sure you have:

- **macOS** (required for SwiftUI development)
- **Xcode 14+** with command line tools
- **Python 3.8+** 
- **Git** for version control
- Basic familiarity with Swift/SwiftUI and Python

### First Time Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Sectionist.git
   cd Sectionist
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/alienbrainfarm/Sectionist.git
   ```

## Development Workflow

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features (when created)
- `feature/issue-name` - Feature branches
- `bugfix/issue-name` - Bug fix branches
- `docs/issue-name` - Documentation-only changes

### Workflow Steps

1. **Sync with upstream**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** (see sections below)

4. **Test your changes** thoroughly

5. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add song segmentation algorithm"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request** on GitHub

## Setting Up Your Development Environment

### Frontend (SwiftUI) ✅ READY TO USE

The frontend is a fully implemented macOS SwiftUI application.

1. **Open the Xcode project**:
   ```bash
   cd Sectionist/  # The SwiftUI project directory
   open Sectionist.xcodeproj
   ```

2. **Build and run** in Xcode (⌘+R)
   - The app will start and attempt to connect to the backend server
   - Make sure the backend is running first (see below)

### Backend (Python) ✅ READY TO USE

The backend is fully implemented with Flask server and audio analysis.

1. **Quick setup with provided script**:
   ```bash
   cd backend/
   ./start_server.sh
   ```
   This script will:
   - Create a virtual environment
   - Install all dependencies
   - Start the server on http://127.0.0.1:5000

2. **Manual setup** (alternative):
   ```bash
   cd backend/
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   pip install -r requirements.txt
   python server.py
   ```

3. **Development dependencies** (for testing and linting):
   ```bash
   pip install -r requirements-dev.txt
   ```

### Audio Processing Dependencies ✅ IMPLEMENTED

The backend uses these libraries:
- `librosa>=0.10.0` - Audio analysis and feature extraction ✅
- `numpy>=1.24.0` - Numerical computing ✅
- `scipy>=1.10.0` - Scientific computing ✅
- `flask>=2.3.0` - Web framework for HTTP API ✅  
- `scipy` - Scientific computing
- `scikit-learn` - Machine learning
- `madmom` - Audio processing (optional)

## Making Changes

### Project Structure (Current Implementation)

```
Sectionist/
├── README.md
├── LICENSE                  # MIT License ✅ IMPLEMENTED
├── CONTRIBUTING.md
├── docs/
│   ├── PRD.md
│   ├── DEVELOPMENT.md
│   ├── CI_CD.md
│   └── COMMUNICATION_PROTOCOL.md
├── Sectionist/              # SwiftUI macOS app ✅ IMPLEMENTED
│   ├── Sectionist.xcodeproj
│   ├── SectionistApp.swift
│   ├── ContentView.swift
│   ├── AnalysisService.swift
│   └── ...
├── backend/                 # Python backend ✅ IMPLEMENTED
│   ├── requirements.txt
│   ├── server.py
│   ├── example.py
│   └── test_*.py
└── scripts/                 # Build and utility scripts (planned)
```

### Areas for Contribution

1. **Audio Analysis** - Enhanced segmentation accuracy, advanced chord detection
2. **SwiftUI Frontend** - Section editing UI, export functionality, settings
3. **Integration** - Performance optimization, error handling, file format support
4. **Testing** - Expanded test coverage, UI testing, performance testing
5. **Documentation** - User guides, API documentation, tutorials
6. **Performance** - Memory optimization, large file handling, real-time processing

## Submitting Changes

### Pull Request Guidelines

1. **Fill out the PR template** (when available)
2. **Write a clear title** describing the change
3. **Include tests** for new functionality
4. **Update documentation** if needed
5. **Keep PRs focused** - one feature/fix per PR
6. **Reference related issues** using keywords like "Fixes #123"

### PR Review Process

1. Automated checks must pass (linting, tests)
2. At least one maintainer review required
3. All conversations must be resolved
4. PR is merged using squash-and-merge

## Code Style

### Swift/SwiftUI

- Follow standard Swift conventions
- Use descriptive variable and function names
- Add documentation comments for public APIs
- Use SwiftUI best practices for state management

Example:
```swift
/// Analyzes audio file and returns song sections
func analyzeSong(from url: URL) async throws -> SongAnalysis {
    // Implementation
}
```

### Python

- Follow **PEP 8** style guide
- Use **Black** for formatting:
  ```bash
  black src/ tests/
  ```
- Use **flake8** for linting:
  ```bash
  flake8 src/ tests/
  ```
- Add type hints where appropriate:
  ```python
  def segment_audio(audio_data: np.ndarray, sample_rate: int) -> List[Segment]:
      """Segment audio into meaningful sections."""
      pass
  ```

### Commit Messages

Use conventional commit format:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Adding/updating tests
- `chore:` - Maintenance tasks

Example: `feat: implement basic song segmentation algorithm`

## Testing

### Frontend Testing

- Use XCTest for unit tests
- Test UI components where appropriate
- Mock backend interactions

### Backend Testing

- Use **pytest** for testing:
  ```bash
  pytest tests/
  ```
- Write unit tests for all analysis functions
- Include integration tests for API endpoints
- Test with various audio formats and edge cases

### Test Coverage

- Aim for >80% test coverage
- Focus on critical paths and edge cases
- Include performance tests for audio processing

## Reporting Issues

### Bug Reports

Include:
- Operating system version
- Xcode version (for frontend issues)
- Python version (for backend issues)
- Steps to reproduce
- Expected vs actual behavior
- Audio file details (format, length, genre) if relevant

### Feature Requests

Include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation approach (if any)
- Mockups or examples (if applicable)

### Questions

- Check existing documentation first
- Search existing issues
- Use descriptive titles
- Provide context for your question

## Getting Help

- **Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Discord/Slack**: [Link when available]

## Recognition

Contributors will be acknowledged in:
- README.md contributors section
- Release notes for significant contributions
- Special recognition for major features

Thank you for contributing to Sectionist! 🎵