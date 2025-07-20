# CI/CD Pipeline

This document describes the continuous integration and continuous deployment (CI/CD) pipeline for the Sectionist project.

## Overview

The CI/CD pipeline is implemented using GitHub Actions and provides automated testing, code quality checks, and integration testing for both the Python backend and SwiftUI frontend components.

## Pipeline Components

### 1. Backend Testing (`test-backend`)
- **Runs on**: Ubuntu Latest
- **Python versions**: 3.10, 3.11, 3.12
- **Features**:
  - Dependency caching for faster builds
  - Code formatting check with Black
  - Linting with Flake8
  - Type checking with MyPy
  - Test execution with pytest
  - Coverage reporting with Codecov

### 2. Frontend Testing (`test-frontend`)
- **Runs on**: macOS Latest
- **Features**:
  - Xcode project building
  - SwiftUI unit and UI tests
  - Derived data caching

### 3. Code Quality (`lint-and-format`)
- **Runs on**: Ubuntu Latest
- **Features**:
  - Black formatting validation
  - Flake8 linting
  - MyPy type checking

### 4. Integration Testing (`integration-tests`)
- **Runs on**: Ubuntu Latest
- **Dependencies**: Requires backend tests to pass
- **Features**:
  - Backend server startup testing
  - Health endpoint validation
  - End-to-end analysis testing

## Workflows

### Main Workflow: `.github/workflows/ci.yml`

Triggers on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

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
   flake8 . --max-line-length=88 --extend-ignore=E203,W503
   ```

3. **MyPy** - Type checking
   ```bash
   cd backend
   mypy .
   ```

4. **Pytest** - Testing with coverage
   ```bash
   cd backend
   pytest -v --cov=. --cov-report=xml --cov-report=term
   ```

### SwiftUI Frontend

1. **Xcode Build**
   ```bash
   cd Sectionist
   xcodebuild -project Sectionist.xcodeproj -scheme Sectionist -configuration Debug build
   ```

2. **Xcode Tests**
   ```bash
   cd Sectionist
   xcodebuild test -project Sectionist.xcodeproj -scheme Sectionist -destination 'platform=macOS'
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
   flake8 . --max-line-length=88 --extend-ignore=E203,W503
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
![CI/CD Pipeline](https://github.com/alienbrainfarm/Sectionist/workflows/CI/CD%20Pipeline/badge.svg)
[![codecov](https://codecov.io/gh/alienbrainfarm/Sectionist/branch/main/graph/badge.svg)](https://codecov.io/gh/alienbrainfarm/Sectionist)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
```

## Environment Variables and Secrets

The pipeline uses these GitHub repository secrets:
- `CODECOV_TOKEN` - For code coverage reporting (optional)

## Performance Optimizations

1. **Dependency Caching**: Uses GitHub Actions cache to speed up dependency installation
2. **Matrix Strategy**: Tests across multiple Python versions in parallel
3. **Derived Data Caching**: Caches Xcode derived data for faster builds

## Troubleshooting

### Common Issues

1. **Backend tests failing**:
   - Check Python version compatibility
   - Ensure all dependencies are listed in `requirements.txt`
   - Verify test data and fixtures

2. **Frontend tests failing**:
   - Check Xcode version compatibility
   - Ensure scheme is configured for testing
   - Verify macOS deployment target

3. **Linting failures**:
   - Run `black .` to auto-format code
   - Check `flake8` output for specific violations
   - Update type hints for MyPy errors

### Local Testing

Before pushing, run the full test suite locally:

```bash
# Backend testing
cd backend
pip install -r requirements.txt -r requirements-dev.txt
black --check .
flake8 . --max-line-length=88 --extend-ignore=E203,W503
mypy .
pytest -v --cov=.

# Frontend testing (macOS only)
cd Sectionist
xcodebuild test -project Sectionist.xcodeproj -scheme Sectionist
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