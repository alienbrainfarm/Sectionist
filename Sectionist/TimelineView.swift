import SwiftUI

struct TimelineView: View {
    let audioFile: URL
    @Binding var isAnalyzing: Bool
    @Binding var sections: [SongSection]
    let onAnalysisComplete: (BackendAnalysisData) -> Void
    
    @State private var currentTime: TimeInterval = 0
    @State private var totalDuration: TimeInterval = 300 // Will be updated from analysis
    @State private var errorMessage: String?
    @State private var showingError = false
    
    @StateObject private var analysisService = AnalysisService.shared
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Timeline")
                .font(.title2)
                .fontWeight(.semibold)
            
            if isAnalyzing {
                AnalyzingPlaceholder()
            } else if sections.isEmpty {
                EmptyTimelineView()
            } else {
                TimelineContent()
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .onAppear {
            if sections.isEmpty {
                // Only load mock data if no real analysis has been done
                loadMockData()
            }
        }
        .alert("Analysis Error", isPresented: $showingError) {
            Button("OK") { }
        } message: {
            Text(errorMessage ?? "An unknown error occurred")
        }
    }
    
    private func loadMockData() {
        // Mock data for demonstration
        sections = [
            SongSection(name: "Intro", startTime: 0, endTime: 15, color: .blue),
            SongSection(name: "Verse 1", startTime: 15, endTime: 45, color: .green),
            SongSection(name: "Chorus", startTime: 45, endTime: 75, color: .orange),
            SongSection(name: "Verse 2", startTime: 75, endTime: 105, color: .green),
            SongSection(name: "Chorus", startTime: 105, endTime: 135, color: .orange),
            SongSection(name: "Bridge", startTime: 135, endTime: 165, color: .purple),
            SongSection(name: "Chorus", startTime: 165, endTime: 195, color: .orange),
            SongSection(name: "Outro", startTime: 195, endTime: 220, color: .red)
        ]
        totalDuration = 220
    }
    
    @ViewBuilder
    private func AnalyzingPlaceholder() -> some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)
            
            Text("Analyzing audio structure...")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, minHeight: 200)
    }
    
    @ViewBuilder
    private func EmptyTimelineView() -> some View {
        VStack(spacing: 16) {
            Image(systemName: "waveform")
                .font(.system(size: 40))
                .foregroundColor(.secondary)
            
            VStack(spacing: 4) {
                Text("No analysis available")
                    .font(.headline)
                
                Text("Analysis results will appear here")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            Button("Analyze Audio") {
                startAnalysis()
            }
            .buttonStyle(.borderedProminent)
            .disabled(isAnalyzing)
        }
        .frame(maxWidth: .infinity, minHeight: 200)
    }
    
    @ViewBuilder
    private func TimelineContent() -> some View {
        VStack(alignment: .leading, spacing: 8) {
            // Time ruler
            HStack {
                ForEach(0..<Int(totalDuration/30) + 1, id: \.self) { index in
                    let time = TimeInterval(index * 30)
                    VStack(alignment: .leading) {
                        Text(formatTime(time))
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Rectangle()
                            .fill(Color.secondary)
                            .frame(width: 1, height: 4)
                    }
                    if index < Int(totalDuration/30) {
                        Spacer()
                    }
                }
            }
            .padding(.horizontal, 4)
            
            // Sections timeline
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 2) {
                    ForEach(sections, id: \.id) { section in
                        SectionBlock(section: section, totalDuration: totalDuration)
                    }
                }
                .padding(.horizontal, 4)
            }
            
            // Playback controls (placeholder)
            HStack {
                Button(action: {}) {
                    Image(systemName: "play.circle.fill")
                        .font(.title)
                }
                
                Button(action: {}) {
                    Image(systemName: "pause.circle.fill")
                        .font(.title)
                }
                
                Slider(value: $currentTime, in: 0...totalDuration) { _ in
                    // Handle scrubbing
                }
                .frame(maxWidth: .infinity)
                
                Text(formatTime(currentTime))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.top, 8)
        }
        .padding()
        .background(Color(.controlBackgroundColor))
        .cornerRadius(8)
    }
    
    private func startAnalysis() {
        Task {
            isAnalyzing = true
            
            do {
                let response = try await analysisService.analyzeAudio(fileURL: audioFile)
                
                await MainActor.run {
                    if let analysisData = response.analysis {
                        // Update local duration for timeline display
                        totalDuration = analysisData.duration
                        
                        // Notify parent about the completion
                        onAnalysisComplete(analysisData)
                        
                        print("Analysis completed: \(sections.count) sections detected")
                        for section in sections {
                            print("  \(section.name): \(section.startTime)s - \(section.endTime)s")
                        }
                    }
                    
                    isAnalyzing = false
                }
                
            } catch {
                await MainActor.run {
                    isAnalyzing = false
                    errorMessage = error.localizedDescription
                    showingError = true
                    print("Analysis error: \(error)")
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

struct SectionBlock: View {
    let section: SongSection
    let totalDuration: TimeInterval
    
    private var blockWidth: CGFloat {
        let sectionDuration = section.endTime - section.startTime
        let ratio = sectionDuration / totalDuration
        return ratio * 400 // Base width for timeline
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Rectangle()
                .fill(section.color)
                .frame(width: blockWidth, height: 30)
                .overlay(
                    Text(section.name)
                        .font(.caption)
                        .foregroundColor(.white)
                        .fontWeight(.medium)
                )
                .cornerRadius(4)
            
            Text(formatTime(section.startTime))
                .font(.caption2)
                .foregroundColor(.secondary)
        }
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

struct SongSection {
    let id = UUID()
    let name: String
    let startTime: TimeInterval
    let endTime: TimeInterval
    let color: Color
}

#Preview {
    TimelineView(
        audioFile: URL(fileURLWithPath: "/sample.mp3"), 
        isAnalyzing: .constant(false),
        sections: .constant([
            SongSection(name: "Intro", startTime: 0, endTime: 15, color: .blue),
            SongSection(name: "Verse", startTime: 15, endTime: 45, color: .green)
        ]),
        onAnalysisComplete: { _ in }
    )
    .frame(width: 400, height: 300)
}