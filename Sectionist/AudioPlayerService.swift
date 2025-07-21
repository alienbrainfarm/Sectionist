import Foundation
import AVFoundation
import SwiftUI

/// Service for handling audio playback functionality in the Sectionist app
///
/// This service manages audio playback using AVFoundation, providing:
/// - Play/pause functionality for audio files
/// - Timeline synchronization with current playback position  
/// - Seeking to specific time positions
/// - Audio session management for macOS
/// - Support for various audio formats (MP3, WAV, M4A, FLAC, etc.)
@MainActor
class AudioPlayerService: NSObject, ObservableObject {
    static let shared = AudioPlayerService()
    
    // MARK: - Published Properties
    @Published var isPlaying: Bool = false
    @Published var currentTime: TimeInterval = 0
    @Published var duration: TimeInterval = 0
    @Published var playbackRate: Float = 1.0
    @Published var errorMessage: String?
    
    // MARK: - Private Properties
    private var audioPlayer: AVAudioPlayer?
    private var playbackTimer: Timer?
    private var currentAudioURL: URL?
    
    // MARK: - Initialization
    private override init() {
        super.init()
        // Note: AVAudioSession is iOS-specific and not needed on macOS
        // AVAudioPlayer handles audio routing automatically on macOS
    }
    
    // MARK: - Public Methods
    
    /// Load an audio file for playback
    /// - Parameter url: The URL of the audio file to load
    func loadAudio(from url: URL) {
        // Stop current playback if any
        stop()
        
        // Store the URL for future reference
        currentAudioURL = url
        
        // Ensure we have access to the security-scoped resource
        guard url.startAccessingSecurityScopedResource() else {
            errorMessage = "Cannot access audio file"
            return
        }
        
        do {
            // Create the audio player
            audioPlayer = try AVAudioPlayer(contentsOf: url)
            audioPlayer?.delegate = self
            audioPlayer?.prepareToPlay()
            audioPlayer?.enableRate = true // Enable playback rate control
            
            // Update duration
            duration = audioPlayer?.duration ?? 0
            currentTime = 0
            
            // Clear any previous errors
            errorMessage = nil
            
            print("Audio loaded successfully: \(url.lastPathComponent)")
            print("Duration: \(duration) seconds")
            
        } catch {
            print("Failed to load audio: \(error.localizedDescription)")
            errorMessage = "Failed to load audio: \(error.localizedDescription)"
            audioPlayer = nil
            
            // Clean up security scoped resource access
            url.stopAccessingSecurityScopedResource()
        }
    }
    
    /// Toggle play/pause state
    func togglePlayback() {
        guard let player = audioPlayer else {
            errorMessage = "No audio file loaded"
            return
        }
        
        if isPlaying {
            pause()
        } else {
            play()
        }
    }
    
    /// Start playback
    func play() {
        guard let player = audioPlayer else {
            errorMessage = "No audio file loaded"
            return
        }
        
        guard player.play() else {
            errorMessage = "Failed to start playback"
            return
        }
        
        isPlaying = true
        player.rate = playbackRate
        startProgressTimer()
        errorMessage = nil
        
        print("Playback started")
    }
    
    /// Pause playback
    func pause() {
        guard let player = audioPlayer else { return }
        
        player.pause()
        isPlaying = false
        stopProgressTimer()
        
        print("Playback paused")
    }
    
    /// Stop playback and reset position
    func stop() {
        guard let player = audioPlayer else { return }
        
        player.stop()
        player.currentTime = 0
        isPlaying = false
        currentTime = 0
        stopProgressTimer()
        
        // Clean up security scoped resource access
        if let url = currentAudioURL {
            url.stopAccessingSecurityScopedResource()
        }
        
        print("Playback stopped")
    }
    
    /// Seek to a specific time position
    /// - Parameter time: The time position to seek to in seconds
    func seek(to time: TimeInterval) {
        guard let player = audioPlayer else { return }
        
        let clampedTime = max(0, min(time, duration))
        player.currentTime = clampedTime
        currentTime = clampedTime
        
        print("Seeked to: \(clampedTime) seconds")
    }
    
    /// Skip backward by specified seconds
    /// - Parameter seconds: Number of seconds to skip backward (default: 10)
    func skipBackward(seconds: TimeInterval = 10) {
        seek(to: currentTime - seconds)
    }
    
    /// Skip forward by specified seconds
    /// - Parameter seconds: Number of seconds to skip forward (default: 10)
    func skipForward(seconds: TimeInterval = 10) {
        seek(to: currentTime + seconds)
    }
    
    /// Set playback rate
    /// - Parameter rate: The playback rate (0.5 to 2.0)
    func setPlaybackRate(_ rate: Float) {
        playbackRate = max(0.5, min(2.0, rate))
        audioPlayer?.rate = playbackRate
        
        print("Playback rate set to: \(playbackRate)")
    }
    
    // MARK: - Private Methods
    
    /// Start the timer for updating current playback position
    private func startProgressTimer() {
        stopProgressTimer() // Ensure no duplicate timers
        
        playbackTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.updateCurrentTime()
            }
        }
    }
    
    /// Stop the progress timer
    private func stopProgressTimer() {
        playbackTimer?.invalidate()
        playbackTimer = nil
    }
    
    /// Update the current playback time
    private func updateCurrentTime() {
        guard let player = audioPlayer else { return }
        currentTime = player.currentTime
    }
    
    // MARK: - Cleanup
    
    deinit {
        stop()
        // Note: AVAudioSession cleanup is iOS-specific and not needed on macOS
    }
}

// MARK: - AVAudioPlayerDelegate

extension AudioPlayerService: AVAudioPlayerDelegate {
    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        Task { @MainActor in
            isPlaying = false
            stopProgressTimer()
            
            if flag {
                print("Audio playback finished successfully")
                // Reset to beginning for potential replay
                seek(to: 0)
            } else {
                print("Audio playback finished with error")
                errorMessage = "Playback ended unexpectedly"
            }
        }
    }
    
    func audioPlayerDecodeErrorDidOccur(_ player: AVAudioPlayer, error: Error?) {
        Task { @MainActor in
            print("Audio player decode error: \(error?.localizedDescription ?? "Unknown error")")
            errorMessage = "Audio decode error: \(error?.localizedDescription ?? "Unknown error")"
            isPlaying = false
            stopProgressTimer()
        }
    }
}

// MARK: - Convenience Extensions

extension AudioPlayerService {
    /// Check if an audio file is currently loaded
    var hasAudioLoaded: Bool {
        return audioPlayer != nil
    }
    
    /// Get formatted current time string
    var formattedCurrentTime: String {
        return formatTime(currentTime)
    }
    
    /// Get formatted duration string
    var formattedDuration: String {
        return formatTime(duration)
    }
    
    /// Get formatted remaining time string
    var formattedRemainingTime: String {
        return formatTime(duration - currentTime)
    }
    
    /// Get current progress as a ratio (0.0 to 1.0)
    var progress: Double {
        guard duration > 0 else { return 0 }
        return currentTime / duration
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}