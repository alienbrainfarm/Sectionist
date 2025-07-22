# Sectionist Frontend-Backend Communication Protocol

This document describes the communication protocol between the Python frontend and Python backend in the Sectionist application.

## Overview

The Sectionist application uses a local HTTP server architecture for communication between components:

- **Frontend**: Python PyQt6 cross-platform application
- **Backend**: Python Flask HTTP server running locally
- **Communication**: HTTP REST API over localhost
- **Data Format**: JSON

## Server Configuration

- **Host**: `127.0.0.1` (localhost)
- **Port**: `5000`
- **Base URL**: `http://127.0.0.1:5000`

## API Endpoints

### 1. Health Check

**Endpoint**: `GET /health`

**Purpose**: Verify that the backend server is running and healthy.

**Request**: No parameters required

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "backend": "python-librosa"
}
```

**Status Codes**:
- `200 OK`: Server is healthy
- `500 Internal Server Error`: Server error

---

### 2. Get Supported Formats

**Endpoint**: `GET /formats`

**Purpose**: Retrieve list of supported audio file formats.

**Request**: No parameters required

**Response**:
```json
{
  "supported_formats": [
    "aac",
    "aif", 
    "aiff",
    "flac",
    "m4a",
    "mp3",
    "ogg",
    "wav"
  ]
}
```

**Status Codes**:
- `200 OK`: Successfully retrieved formats
- `500 Internal Server Error`: Server error

---

### 3. Analyze Audio File

**Endpoint**: `POST /analyze`

**Purpose**: Upload and analyze an audio file to extract musical information.

**Request**:
- **Method**: POST
- **Content-Type**: `multipart/form-data`
- **Body**: Form data with file upload
  - `audio`: Audio file (binary data)

**Example Request**:
```bash
curl -X POST -F 'audio=@/path/to/song.mp3' http://127.0.0.1:5000/analyze
```

**Successful Response**:
```json
{
  "success": true,
  "file_name": "song.mp3",
  "analysis": {
    "duration": 180.5,
    "tempo": 120.3,
    "key": "C major", 
    "sections": [
      {
        "name": "Intro",
        "start": 0.0,
        "end": 12.5,
        "confidence": 0.95
      },
      {
        "name": "Verse 1", 
        "start": 12.5,
        "end": 32.0,
        "confidence": 0.87
      },
      {
        "name": "Chorus",
        "start": 32.0,
        "end": 52.5,
        "confidence": 0.92
      }
    ],
    "beats_detected": 360
  }
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "Unsupported file format. Supported formats: mp3, wav, aiff, m4a, flac, ogg, aac"
}
```

**Status Codes**:
- `200 OK`: Analysis completed successfully
- `400 Bad Request`: Invalid request (no file, unsupported format, etc.)
- `500 Internal Server Error`: Analysis failed or server error

## Data Models

### Analysis Response Structure

```typescript
interface AnalysisResponse {
  success: boolean;
  file_name?: string;
  analysis?: AnalysisData;
  error?: string;
}

interface AnalysisData {
  duration: number;        // Song duration in seconds
  tempo: number;           // Estimated tempo in BPM
  key: string;            // Detected musical key (e.g., "C major")
  sections: SongSection[]; // Detected song sections
  beats_detected: number;  // Number of beats detected
}

interface SongSection {
  name: string;           // Section name (e.g., "Intro", "Verse 1", "Chorus")
  start: number;          // Start time in seconds
  end: number;            // End time in seconds  
  confidence: number;     // Confidence score (0.0 - 1.0)
}
```

## Swift Implementation

### HTTP Client Service

The current Python frontend includes HTTP communication functionality that handles all backend requests, while the archived SwiftUI frontend used an `AnalysisService` class.

```swift
class AnalysisService: ObservableObject {
    static let shared = AnalysisService()
    private let baseURL = "http://127.0.0.1:5000"
    
    // Health check
    func checkHealth() async throws -> ServerHealth
    
    // Get supported formats
    func getSupportedFormats() async throws -> SupportedFormats
    
    // Analyze audio file
    func analyzeAudio(fileURL: URL) async throws -> AnalysisResponse
}
```

### Error Handling

The Swift client provides comprehensive error handling:

```swift
enum AnalysisError: LocalizedError {
    case invalidURL
    case fileNotFound
    case fileAccessError(String)
    case fileReadError(String)  
    case networkError(String)
    case serverError(String)
    case analysisError(String)
}
```

## Usage Flow

1. **Start Backend Server**:
   ```bash
   cd backend
   source venv/bin/activate
   python server.py
   ```

2. **SwiftUI Application**:
   - User drags/selects audio file
   - App checks server health (`/health`)
   - App uploads file for analysis (`/analyze`)
   - App receives structured analysis results
   - App updates UI with sections and analysis data

3. **Data Transformation**:
   - Backend analysis results are converted to SwiftUI models
   - Song sections are mapped to timeline visualization
   - Analysis data populates results view

## File Size and Format Limits

- **Maximum file size**: 100MB
- **Supported formats**: MP3, WAV, AIFF, M4A, FLAC, OGG, AAC
- **Typical processing time**: 30-60 seconds for 4-minute songs

## Security Considerations

- Server runs on localhost only (127.0.0.1)
- No authentication required (local development only)
- Files are processed temporarily and cleaned up
- SwiftUI handles sandbox security-scoped resources

## Error Scenarios

1. **Backend server not running**:
   - Network error in SwiftUI
   - User shown error message to start backend

2. **Unsupported file format**:
   - 400 error from backend
   - Clear error message to user

3. **Analysis failure**:
   - 500 error from backend
   - Generic analysis error message

4. **Network timeout**:
   - Request timeout (60 seconds)
   - Retry option for user

## Future Enhancements

- WebSocket support for real-time progress updates
- Authentication for remote deployment
- Batch processing capabilities
- Analysis caching and persistence
- Advanced chord detection and key change analysis