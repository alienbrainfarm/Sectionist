#!/usr/bin/env python3
"""
Sectionist Backend HTTP Server

This Flask server provides REST API endpoints for the Sectionist SwiftUI frontend
to communicate with the Python audio analysis backend.

Endpoints:
- POST /analyze - Analyze an audio file and return structured results
- GET /health - Health check endpoint
- GET /status/<task_id> - Check analysis status (future enhancement)

The server runs locally and processes audio files for song structure analysis,
key detection, and tempo estimation.
"""

import os
import sys
import traceback
import tempfile
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from example import analyze_audio_file

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = tempfile.gettempdir()
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
ALLOWED_EXTENSIONS = {"mp3", "wav", "aiff", "aif", "m4a", "flac", "ogg", "aac"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify server is running."""
    return jsonify(
        {"status": "healthy", "version": "1.0.0", "backend": "python-librosa"}
    )


@app.route("/analyze", methods=["POST"])
def analyze_audio():
    """
    Analyze an uploaded audio file and return structured results.

    Expected request:
    - Method: POST
    - Content-Type: multipart/form-data
    - Body: file with key 'audio'

    Returns:
    - JSON response with analysis results or error message
    """
    try:
        # Check if request has file
        if "audio" not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        file = request.files["audio"]

        # Check if file was actually selected
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Check file type
        if not allowed_file(file.filename):
            formats = ", ".join(ALLOWED_EXTENSIONS)
            error_msg = f"Unsupported file format. Supported formats: {formats}"
            return jsonify({"error": error_msg}), 400

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(temp_path)

        try:
            # Analyze the audio file
            print(f"Analyzing file: {temp_path}")
            results = analyze_audio_file(temp_path)

            # Convert analysis results to the format expected by SwiftUI frontend
            response_data = {
                "success": True,
                "file_name": filename,
                "analysis": {
                    "duration": results["duration"],
                    "tempo": results["tempo"],
                    "key": results["key"],
                    "key_changes": results["key_changes"],
                    "sections": results["sections"],
                    "beats_detected": results["beats_detected"],
                    "chords": results["chords"],
                },
            }

            print(f"Analysis completed successfully for {filename}")
            return jsonify(response_data)

        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass  # Ignore cleanup errors

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Analysis failed: {str(e)}"}), 500


@app.route("/formats", methods=["GET"])
def supported_formats():
    """Return list of supported audio formats."""
    return jsonify({"supported_formats": sorted(list(ALLOWED_EXTENSIONS))})


def main():
    """Main function to run the Flask server."""
    print("🎵 Sectionist Backend Server")
    print("=" * 30)
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📏 Max file size: {MAX_CONTENT_LENGTH // (1024*1024)}MB")
    print(f"🎶 Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    print()

    # Check if librosa is available
    try:
        import librosa  # noqa: F401

        print("✅ librosa available")
    except ImportError:
        print("❌ librosa not available. Run: pip install -r requirements.txt")
        sys.exit(1)

    port = 5000
    host = "127.0.0.1"

    print(f"🚀 Starting server on http://{host}:{port}")
    print("📡 Available endpoints:")
    print(f"   GET  http://{host}:{port}/health")
    print(f"   POST http://{host}:{port}/analyze")
    print(f"   GET  http://{host}:{port}/formats")
    print()
    print("💡 To test the server:")
    print(f"   curl http://{host}:{port}/health")
    print(f"   curl -X POST -F 'audio=@/path/to/song.mp3' http://{host}:{port}/analyze")
    print()

    # Run the Flask development server
    app.run(host=host, port=port, debug=True)


if __name__ == "__main__":
    main()
