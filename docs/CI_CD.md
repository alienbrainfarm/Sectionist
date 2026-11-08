# CI/CD Pipeline

This document describes the continuous integration and continuous deployment (CI/CD) pipeline for the Sectionist project.

## Overview

The CI/CD pipeline is implemented using GitHub Actions and provides automated testing, code quality checks, and integration testing for the Python backend and Python frontend components.

## Pipeline Components

### 1. Backend Testing (`backend-tests`)
- **Runs on**: Ubuntu Latest
- **Python versions**: 3.10, 3.11, 3.12
- **Features**:
  - Dependency caching for faster builds
  - Linting with Flake8 (88-character lines, configured in `.flake8`)
  - Code formatting check with Black
  - Test execution with pytest
  - Coverage reporting with Codecov (Python 3.11 only)

### 2. Frontend Testing (`frontend-tests`)
- **Runs on**: Ubuntu Latest
- **Python version**: 3.11
- **Features**:
  - Installation of Qt and libvlc system libraries
  - Linting with Flake8 and formatting check with Black
  - PyQt6 unit and integration tests
  - Headless execution with `QT_QPA_PLATFORM=offscreen`

### 3. Integration Testing (`integration-tests`)
- **Runs on**: Ubuntu Latest
- **Python version**: 3.11
- **Dependencies**: Requires backend tests to pass
- **Features**:
  - Backend server startup testing
  - Health endpoint validation (`/health`)
  - Supported formats endpoint validation (`/formats`)
  - End-to-end analysis testing with `backend/smoke_test.py`

## Workflows

### Main Workflow: `.github/workflows/ci.yml`

Triggers on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual runs via `workflow_dispatch`

## Code Quality Tools

### Python Backend

1. **Black** - Code formatting
   ```bash
   cd backend
   black .
   ```

2. **Flake8** - Linting
   ```bash
   cd backend
   flake8 .
   ```

3. **MyPy** - Optional local type checking (not run in CI)
   ```bash
   cd backend
   mypy .
   ```

4. **Pytest** - Testing with coverage
   ```bash
   cd backend
   pytest -v --cov=. --cov-report=xml --cov-report=term
   ```

### Python Frontend

1. **Pytest** - Headless UI and integration tests
   ```bash
   cd frontend
   QT_QPA_PLATFORM=offscreen pytest -v
   ```

2. **System libraries** - Qt needs a rendering backend, and python-vlc needs
   libvlc at import time:
   ```bash
   sudo apt-get install -y libgl1 libegl1 libxkbcommon0 libvlc5 libvlccore9
   ```

## Pre-commit Hooks

The project includes pre-commit hooks configuration (`.pre-commit-config.yaml`) to ensure code quality:

1. **Install pre-commit**:
   ```bash
   pip install pre-commit
   ```

2. **Install hooks**:
   ```bash
   pre-commit install
   ```

3. **Run hooks manually**:
   ```bash
   pre-commit run --all-files
   ```

## Development Workflow

1. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and ensure code quality**:
   ```bash
   cd backend
   black .
   flake8 .
   pytest -v --cov=.
   ```

3. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name
   ```

4. **Open Pull Request** - CI/CD pipeline will run automatically

## Status Badges

Add these badges to your README to show build status:

```markdown
![CI](https://github.com/alienbrainfarm/Sectionist/workflows/CI/badge.svg)
[![codecov](https://codecov.io/gh/alienbrainfarm/Sectionist/branch/main/graph/badge.svg)](https://codecov.io/gh/alienbrainfarm/Sectionist)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
```

## Environment Variables and Secrets

The pipeline uses these GitHub repository secrets:
- `CODECOV_TOKEN` - For code coverage reporting (optional)

## Performance Optimizations

1. **Dependency Caching**: Uses GitHub Actions cache to speed up dependency installation
2. **Matrix Strategy**: Tests across multiple Python versions in parallel
3. **Headless Frontend Tests**: Qt runs with `QT_QPA_PLATFORM=offscreen`, so no display server is required

## Troubleshooting

### Common Issues

1. **Backend tests failing**:
   - Check Python version compatibility
   - Ensure all dependencies are listed in `requirements.txt`
   - Verify test data and fixtures

2. **Frontend tests failing**:
   - Check that Qt and libvlc system libraries are installed
   - Ensure `QT_QPA_PLATFORM=offscreen` is set for headless runs
   - Confirm the backend is not required for the test being run

3. **Linting failures**:
   - Run `black .` to auto-format code
   - Check `flake8` output for specific violations
   - Review `pyproject.toml` and `.flake8` for the configured 88-character line length

### Local Testing

Before pushing, run the full test suite locally:

```bash
# Backend testing
cd backend
pip install -r requirements.txt -r requirements-dev.txt
black --check .
flake8 .
mypy .
pytest -v --cov=.

# Frontend testing (headless)
cd frontend
pip install -r requirements.txt
QT_QPA_PLATFORM=offscreen pytest -v
```

## Contributing

When contributing to the CI/CD pipeline:

1. Test changes in a fork first
2. Update this documentation for any workflow changes
3. Ensure backwards compatibility
4. Consider impact on build times and resource usage

## Future Improvements

Planned enhancements for the CI/CD pipeline:

- [ ] Automated dependency updates with Dependabot
- [ ] Security scanning with CodeQL
- [ ] Performance benchmarking
- [ ] Automated releases and changelog generation
- [ ] Container-based testing environments
- [ ] Integration with external testing services
