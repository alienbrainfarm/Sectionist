import SwiftUI

struct AnalysisResultsView: View {
    let audioFile: URL
    @Binding var isAnalyzing: Bool
    @Binding var analysisResults: AnalysisData?
    
    @State private var errorMessage: String?
    @State private var showingError = false
    
    @StateObject private var analysisService = AnalysisService.shared
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Analysis Results")
                .font(.title2)
                .fontWeight(.semibold)
            
            if isAnalyzing {
                AnalyzingPlaceholder()
            } else if let results = analysisResults {
                AnalysisContent(results: results)
            } else {
                EmptyAnalysisView()
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .onAppear {
            if analysisResults == nil {
                // Only load mock data if no real analysis has been done
                loadMockAnalysisData()
            }
        }
        .alert("Analysis Error", isPresented: $showingError) {
            Button("OK") { }
        } message: {
            Text(errorMessage ?? "An unknown error occurred")
        }
    }
    
    private func loadMockAnalysisData() {
        // Mock analysis data
        analysisResults = AnalysisData(
            detectedKey: "C Major",
            bpm: 120,
            keyChanges: [
                KeyChange(time: 90, newKey: "F Major"),
                KeyChange(time: 165, newKey: "C Major")
            ],
            chordProgression: [
                ChordInfo(startTime: 0, chord: "C", duration: 2.0),
                ChordInfo(startTime: 2, chord: "Am", duration: 2.0),
                ChordInfo(startTime: 4, chord: "F", duration: 2.0),
                ChordInfo(startTime: 6, chord: "G", duration: 2.0)
            ]
        )
    }
    
    @ViewBuilder
    private func AnalyzingPlaceholder() -> some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)
            
            Text("Analyzing harmonics and structure...")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, minHeight: 200)
    }
    
    @ViewBuilder
    private func EmptyAnalysisView() -> some View {
        VStack(spacing: 16) {
            Image(systemName: "music.quarternote.3")
                .font(.system(size: 40))
                .foregroundColor(.secondary)
            
            VStack(spacing: 4) {
                Text("No analysis data")
                    .font(.headline)
                
                Text("Key, tempo, and chord information will appear here")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
        }
        .frame(maxWidth: .infinity, minHeight: 200)
    }
    
    @ViewBuilder
    private func AnalysisContent(results: AnalysisData) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Key and Tempo Information
                KeyTempoSection(results: results)
                
                Divider()
                
                // Key Changes
                if !results.keyChanges.isEmpty {
                    KeyChangesSection(keyChanges: results.keyChanges)
                    Divider()
                }
                
                // Chord Progression
                ChordProgressionSection(chords: results.chordProgression)
            }
            .padding()
        }
        .background(Color(.controlBackgroundColor))
        .cornerRadius(8)
    }
}

struct KeyTempoSection: View {
    let results: AnalysisData
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Key & Tempo")
                .font(.headline)
            
            HStack(spacing: 24) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Key")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(results.detectedKey)
                        .font(.title3)
                        .fontWeight(.semibold)
                        .foregroundColor(.blue)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    Text("Tempo")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text("\(results.bpm) BPM")
                        .font(.title3)
                        .fontWeight(.semibold)
                        .foregroundColor(.green)
                }
                
                Spacer()
            }
        }
    }
}

struct KeyChangesSection: View {
    let keyChanges: [KeyChange]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Key Changes")
                .font(.headline)
            
            VStack(alignment: .leading, spacing: 8) {
                ForEach(keyChanges, id: \.id) { change in
                    HStack {
                        Image(systemName: "arrow.right.circle.fill")
                            .foregroundColor(.orange)
                        
                        Text("at \(formatTime(change.time))")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Text("→ \(change.newKey)")
                            .font(.subheadline)
                            .fontWeight(.medium)
                        
                        Spacer()
                    }
                }
            }
        }
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

struct ChordProgressionSection: View {
    let chords: [ChordInfo]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Chord Progression")
                .font(.headline)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 4), count: 4), spacing: 8) {
                ForEach(chords.prefix(16), id: \.id) { chord in
                    ChordBlock(chord: chord)
                }
            }
            
            if chords.count > 16 {
                Text("... and \(chords.count - 16) more chords")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.top, 4)
            }
        }
    }
}

struct ChordBlock: View {
    let chord: ChordInfo
    
    var body: some View {
        VStack(spacing: 2) {
            Text(chord.chord)
                .font(.headline)
                .fontWeight(.bold)
                .foregroundColor(.white)
            
            Text(formatTime(chord.startTime))
                .font(.caption2)
                .foregroundColor(.white.opacity(0.8))
        }
        .frame(width: 60, height: 50)
        .background(Color.blue.gradient)
        .cornerRadius(6)
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

struct AnalysisData {
    let detectedKey: String
    let bpm: Int
    let keyChanges: [KeyChange]
    let chordProgression: [ChordInfo]
}

struct KeyChange {
    let id = UUID()
    let time: TimeInterval
    let newKey: String
}

struct ChordInfo {
    let id = UUID()
    let startTime: TimeInterval
    let chord: String
    let duration: TimeInterval
}

#Preview {
    AnalysisResultsView(
        audioFile: URL(fileURLWithPath: "/sample.mp3"), 
        isAnalyzing: .constant(false),
        analysisResults: .constant(AnalysisData(
            detectedKey: "C Major",
            bpm: 120,
            keyChanges: [],
            chordProgression: []
        ))
    )
    .frame(width: 300, height: 500)
}