import Foundation
import SwiftUI

/// Service for communicating with the Sectionist Python backend server
class AnalysisService: ObservableObject {
    static let shared = AnalysisService()
    
    private let baseURL = "http://127.0.0.1:5000"
    private let session = URLSession.shared
    
    private init() {}
    
    /// Check if the backend server is healthy and reachable
    func checkHealth() async throws -> ServerHealth {
        guard let url = URL(string: "\(baseURL)/health") else {
            throw AnalysisError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw AnalysisError.serverError("Server returned error status")
        }
        
        return try JSONDecoder().decode(ServerHealth.self, from: data)
    }
    
    /// Get supported audio formats from the backend
    func getSupportedFormats() async throws -> SupportedFormats {
        guard let url = URL(string: "\(baseURL)/formats") else {
            throw AnalysisError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw AnalysisError.serverError("Failed to get supported formats")
        }
        
        return try JSONDecoder().decode(SupportedFormats.self, from: data)
    }
    
    /// Analyze an audio file and return structured results
    func analyzeAudio(fileURL: URL) async throws -> AnalysisResponse {
        guard let url = URL(string: "\(baseURL)/analyze") else {
            throw AnalysisError.invalidURL
        }
        
        // Check if file exists and is accessible
        guard fileURL.startAccessingSecurityScopedResource() else {
            throw AnalysisError.fileAccessError("Cannot access file")
        }
        
        defer {
            fileURL.stopAccessingSecurityScopedResource()
        }
        
        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            throw AnalysisError.fileNotFound
        }
        
        // Create multipart form data request
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        // Create request body
        let httpBody = NSMutableData()
        
        // Add file data
        httpBody.append("--\(boundary)\r\n".data(using: .utf8)!)
        httpBody.append("Content-Disposition: form-data; name=\"audio\"; filename=\"\(fileURL.lastPathComponent)\"\r\n".data(using: .utf8)!)
        httpBody.append("Content-Type: audio/\(fileURL.pathExtension)\r\n\r\n".data(using: .utf8)!)
        
        do {
            let fileData = try Data(contentsOf: fileURL)
            httpBody.append(fileData)
        } catch {
            throw AnalysisError.fileReadError("Could not read audio file: \(error.localizedDescription)")
        }
        
        httpBody.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        
        request.httpBody = httpBody as Data
        
        // Set timeout for large files
        request.timeoutInterval = 60.0
        
        do {
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw AnalysisError.networkError("Invalid response")
            }
            
            if httpResponse.statusCode != 200 {
                // Try to parse error response
                if let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                    throw AnalysisError.serverError(errorResponse.error)
                } else {
                    throw AnalysisError.serverError("Server returned status \(httpResponse.statusCode)")
                }
            }
            
            let analysisResponse = try JSONDecoder().decode(AnalysisResponse.self, from: data)
            
            if !analysisResponse.success {
                throw AnalysisError.analysisError(analysisResponse.error ?? "Analysis failed")
            }
            
            return analysisResponse
            
        } catch let error as AnalysisError {
            throw error
        } catch {
            throw AnalysisError.networkError("Network request failed: \(error.localizedDescription)")
        }
    }
}

// MARK: - Data Models

struct ServerHealth: Codable {
    let status: String
    let version: String
    let backend: String
}

struct SupportedFormats: Codable {
    let supportedFormats: [String]
    
    enum CodingKeys: String, CodingKey {
        case supportedFormats = "supported_formats"
    }
}

struct AnalysisResponse: Codable {
    let success: Bool
    let fileName: String?
    let analysis: BackendAnalysisData?
    let error: String?
    
    enum CodingKeys: String, CodingKey {
        case success
        case fileName = "file_name"
        case analysis
        case error
    }
}

struct BackendAnalysisData: Codable {
    let duration: Double
    let tempo: Double
    let key: String
    let sections: [BackendSongSection]
    let beatsDetected: Int
    let keyChanges: [BackendKeyChange]
    let chords: [BackendChord]
    
    enum CodingKeys: String, CodingKey {
        case duration, tempo, key, sections
        case beatsDetected = "beats_detected"
        case keyChanges = "key_changes"
        case chords
    }
}

struct BackendSongSection: Codable {
    let name: String
    let start: Double
    let end: Double
    let confidence: Double
}

struct BackendKeyChange: Codable {
    let timestamp: Double
    let fromKey: String
    let toKey: String
    let confidence: Double
    
    enum CodingKeys: String, CodingKey {
        case timestamp
        case fromKey = "from_key"
        case toKey = "to_key"
        case confidence
    }
}

struct BackendChord: Codable {
    let name: String
    let start: Double
    let end: Double
    let confidence: Double
}

struct ErrorResponse: Codable {
    let error: String
}

// MARK: - Errors

enum AnalysisError: LocalizedError {
    case invalidURL
    case fileNotFound
    case fileAccessError(String)
    case fileReadError(String)
    case networkError(String)
    case serverError(String)
    case analysisError(String)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid server URL"
        case .fileNotFound:
            return "Audio file not found"
        case .fileAccessError(let message):
            return "File access error: \(message)"
        case .fileReadError(let message):
            return "File read error: \(message)"
        case .networkError(let message):
            return "Network error: \(message)"
        case .serverError(let message):
            return "Server error: \(message)"
        case .analysisError(let message):
            return "Analysis error: \(message)"
        }
    }
}

// MARK: - Extension for Converting Backend Data to Frontend Models

extension BackendAnalysisData {
    /// Convert backend analysis data to frontend AnalysisData model
    func toAnalysisData() -> AnalysisData {
        return AnalysisData(
            detectedKey: key,
            bpm: Int(tempo.rounded()),
            keyChanges: keyChanges.map { backendKeyChange in
                KeyChange(time: backendKeyChange.timestamp, newKey: backendKeyChange.toKey)
            },
            chordProgression: chords.map { backendChord in
                ChordInfo(
                    startTime: backendChord.start,
                    chord: backendChord.name,
                    duration: backendChord.end - backendChord.start
                )
            }
        )
    }
    
    /// Convert backend sections to frontend song sections
    func toSongSections() -> [SongSection] {
        return sections.enumerated().map { index, section in
            SongSection(
                name: section.name,
                startTime: section.start,
                endTime: section.end,
                color: colorForSection(section.name, index: index),
                isUserEdited: false
            )
        }
    }
    
    /// Get appropriate color for section type
    private func colorForSection(_ name: String, index: Int) -> Color {
        let lowercased = name.lowercased()
        
        if lowercased.contains("intro") {
            return .blue
        } else if lowercased.contains("verse") {
            return .green
        } else if lowercased.contains("chorus") {
            return .orange
        } else if lowercased.contains("bridge") {
            return .purple
        } else if lowercased.contains("outro") {
            return .red
        } else {
            // Fallback to cycling through colors
            let colors: [Color] = [.cyan, .mint, .indigo, .pink, .yellow]
            return colors[index % colors.count]
        }
    }
}