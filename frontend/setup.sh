#!/bin/bash
# Setup script for Sectionist Python Frontend

set -e

echo "🎵 Sectionist Python Frontend Setup"
echo "===================================="

# Check Python version
python3 --version || {
    echo "❌ Python 3 is required but not installed."
    exit 1
}

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To run the Python frontend:"
echo "   cd frontend"
echo "   source venv/bin/activate"
echo "   python sectionist_gui.py"
echo ""
echo "📋 Prerequisites:"
echo "   • Install the VLC media player application (provides libvlc)"
echo "   • Start the backend server first (see ../backend/start_server.sh)"
echo "   • Make sure you have audio files to test with"
echo ""
echo "🖥️ Supported platforms:"
echo "   • Windows 10/11"
echo "   • macOS 10.14+"
echo "   • Linux (Ubuntu 20.04+, Fedora 33+, etc.)"