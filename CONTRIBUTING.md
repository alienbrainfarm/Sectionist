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

- **Python 3.8+** (primary development language)
- **Git** for version control
- Basic familiarity with Python and PyQt6
- Cross-platform development environment (Windows, macOS, or Linux)

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

### Frontend (Python/PyQt6) ✅ ACTIVE DEVELOPMENT

The frontend is a cross-platform Python application using PyQt6.

1. **Set up the Python frontend**:
   ```bash
   cd frontend/
   ./setup.sh  # Automated setup script
   ```
   
   Or manually:
   ```bash
   cd frontend/
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the frontend**:
   ```bash
   cd frontend/
   source venv/bin/activate
   python sectionist_gui.py
   ```

### Swift Frontend (Archived) 📦 REFERENCE ONLY

The original Swift implementation has been moved to `Swift-frontend-archived/` for reference. It is no longer actively developed but remains available for historical purposes and reference.

### Backend (Python) ✅ ACTIVE DEVELOPMENT

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
├── frontend/                # Python frontend ✅ ACTIVE DEVELOPMENT
│   ├── sectionist_gui.py   # Main PyQt6 application
│   ├── requirements.txt
│   ├── setup.sh
│   └── README.md
├── Swift-frontend-archived/ # Archived Swift code 📦 REFERENCE ONLY
│   ├── Sectionist.xcodeproj # (archived)
│   ├── SectionistApp.swift  # (archived)
│   └── ...                  # (archived)
├── backend/                 # Python backend ✅ ACTIVE DEVELOPMENT
│   ├── requirements.txt
│   ├── server.py
│   ├── example.py
│   └── test_*.py
└── scripts/                 # Build and utility scripts (planned)
```

### Areas for Contribution

1. **Python Frontend** - Enhanced UI/UX, section editing features, local database integration
2. **Audio Analysis** - Enhanced segmentation accuracy, advanced chord detection, bar detection
3. **Cross-Platform** - Platform-specific optimizations, improved file handling
4. **Testing** - Expanded test coverage, UI testing, performance testing
5. **Documentation** - User guides, API documentation, tutorials
6. **Performance** - Memory optimization, large file handling, real-time processing

### Current Priority Areas (Based on Project Goals)

1. **🎨 Enhanced Frontend Look and Feel** - Improve UI design and user experience
2. **✏️ More Intuitive Editing Features** - Add section editing and manipulation tools
3. **💾 Local Database Integration** - Implement SQLite for storing song modifications
4. **📊 Bar Detection and Display** - Add musical bar/measure detection and visualization

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

### Python

- Follow **PEP 8** style guidelines
- Use **black** for automatic formatting
- Use **descriptive variable and function names**
- Add **docstrings** for classes and functions
- Use **type hints** where appropriate

Example:
```python
def analyze_song(file_path: str) -> SongAnalysis:
    """
    Analyzes audio file and returns song sections.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        SongAnalysis object containing detected sections
    """
    # Implementation here
    pass
```

### Swift (Archived - For Reference Only)

The Swift code in `Swift-frontend-archived/` follows standard Swift conventions but is no longer actively maintained.
    // Implementation
}
```

### Formatting and Linting

Use the development tools:
```bash
# Backend/Frontend Python code
cd backend/ # or frontend/
source venv/bin/activate

# Format code
black .

# Lint code  
flake8 .

# Type checking
mypy .
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

### Frontend Testing (Python)

- Use **pytest** for Python frontend testing:
  ```bash
  cd frontend/
  source venv/bin/activate
  pytest tests/
  ```
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
- Operating system and version (Windows, macOS, Linux)
- Python version
- Browser (if applicable)
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