#!/bin/bash

# Sectionist Backend Startup Script
# This script sets up and starts the Sectionist Python backend server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"

echo "🎵 Sectionist Backend Setup & Startup"
echo "======================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if we're in the backend directory
if [[ ! -f "$BACKEND_DIR/requirements.txt" ]]; then
    echo "❌ requirements.txt not found. Make sure you're running this from the backend directory."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [[ ! -d "$BACKEND_DIR/venv" ]]; then
    echo "🔧 Creating Python virtual environment..."
    python3 -m venv "$BACKEND_DIR/venv"
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$BACKEND_DIR/venv/bin/activate"

# Install/update dependencies
echo "🔧 Installing Python dependencies..."
pip install -r "$BACKEND_DIR/requirements.txt" > /dev/null

# Check if librosa is working
echo "🔧 Checking librosa installation..."
if python3 -c "import librosa; print('librosa version:', librosa.__version__)" 2>/dev/null; then
    echo "✅ librosa is working correctly"
else
    echo "❌ librosa is not working. Trying to reinstall..."
    pip install --force-reinstall librosa
fi

echo ""
echo "🚀 Starting Sectionist Backend Server..."
echo ""
echo "📡 The server will be available at: http://127.0.0.1:5000"
echo "🛑 To stop the server, press Ctrl+C"
echo ""

# Start the Flask server
python3 "$BACKEND_DIR/server.py"