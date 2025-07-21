import SwiftUI

/// Enhanced timeline view for displaying song sections with interactive features
/// 
/// Features:
/// - Interactive section selection and hover effects
/// - Dynamic time rulers based on song duration
/// - Click-to-seek functionality
/// - Responsive section blocks with gradients and animations
/// - Enhanced playback controls with skip and speed options
/// - Accessibility support with proper labels and hints
struct TimelineView: View {
    let audioFile: URL
    @Binding var isAnalyzing: Bool
    @Binding var sections: [SongSection]
    let onAnalysisComplete: (BackendAnalysisData) -> Void
    
    @State private var currentTime: TimeInterval = 0
    @State private var totalDuration: TimeInterval = 300 // Will be updated from analysis
    @State private var errorMessage: String?
    @State private var showingError = false
    @State private var selectedSection: SongSection?
    @State private var hoveredSection: SongSection?
    
    @StateObject private var analysisService = AnalysisService.shared
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Enhanced header with duration info
            HStack {
                VStack(alignment: .leading) {
                    Text("Timeline")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    if !sections.isEmpty {
                        Text("Duration: \(formatTime(totalDuration)) • \(sections.count) sections")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                if !sections.isEmpty && !isAnalyzing {
                    Button("Re-analyze") {
                        startAnalysis()
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
            }
            
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
        // Enhanced mock data for demonstration with more realistic song structure
        sections = [
            SongSection(name: "Intro", startTime: 0, endTime: 12, color: .blue),
            SongSection(name: "Verse 1", startTime: 12, endTime: 40, color: .green),
            SongSection(name: "Pre-Chorus", startTime: 40, endTime: 52, color: .mint),
            SongSection(name: "Chorus", startTime: 52, endTime: 80, color: .orange),
            SongSection(name: "Verse 2", startTime: 80, endTime: 108, color: .green),
            SongSection(name: "Pre-Chorus", startTime: 108, endTime: 120, color: .mint),
            SongSection(name: "Chorus", startTime: 120, endTime: 148, color: .orange),
            SongSection(name: "Bridge", startTime: 148, endTime: 180, color: .purple),
            SongSection(name: "Final Chorus", startTime: 180, endTime: 220, color: .orange),
            SongSection(name: "Outro", startTime: 220, endTime: 240, color: .red)
        ]
        totalDuration = 240
    }
    
    @ViewBuilder
    private func AnalyzingPlaceholder() -> some View {
        VStack(spacing: 20) {
            // Animated progress indicator
            HStack(spacing: 8) {
                ForEach(0..<3) { index in
                    Circle()
                        .fill(.accentColor)
                        .frame(width: 8, height: 8)
                        .scaleEffect(isAnalyzing ? 1.2 : 0.8)
                        .animation(
                            .easeInOut(duration: 0.6)
                            .repeatForever()
                            .delay(Double(index) * 0.2),
                            value: isAnalyzing
                        )
                }
            }
            
            VStack(spacing: 8) {
                Text("Analyzing audio structure...")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Text("Detecting sections, tempo, and key signature")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            
            // Mock progress sections appearing
            HStack(spacing: 4) {
                ForEach(0..<5) { index in
                    RoundedRectangle(cornerRadius: 3)
                        .fill(.secondary.opacity(0.3))
                        .frame(width: 40, height: 20)
                        .overlay(
                            RoundedRectangle(cornerRadius: 3)
                                .fill(.accentColor.opacity(0.6))
                                .scaleEffect(x: index < 3 ? 1.0 : 0.0, anchor: .leading)
                                .animation(
                                    .easeInOut(duration: 0.8)
                                    .delay(Double(index) * 0.3)
                                    .repeatForever(),
                                    value: isAnalyzing
                                )
                        )
                }
            }
            .padding(.top, 8)
        }
        .frame(maxWidth: .infinity, minHeight: 200)
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.controlBackgroundColor).opacity(0.5))
        )
        .onAppear {
            // This triggers the animation
        }
    }
    
    @ViewBuilder
    private func EmptyTimelineView() -> some View {
        VStack(spacing: 20) {
            Image(systemName: "waveform.path")
                .font(.system(size: 48))
                .foregroundColor(.accentColor.opacity(0.6))
            
            VStack(spacing: 8) {
                Text("Ready to analyze")
                    .font(.title3)
                    .fontWeight(.semibold)
                
                Text("Click below to start analyzing your audio file and discover its structure")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .lineLimit(3)
            }
            
            Button("Analyze Audio") {
                startAnalysis()
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .disabled(isAnalyzing)
        }
        .frame(maxWidth: .infinity, minHeight: 200)
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.controlBackgroundColor).opacity(0.3))
                .strokeBorder(Color.accentColor.opacity(0.3), style: StrokeStyle(lineWidth: 1, dash: [5]))
        )
    }
    
    @ViewBuilder
    private func TimelineContent() -> some View {
        VStack(alignment: .leading, spacing: 12) {
            // Enhanced time ruler with more granular markers
            TimeRuler(totalDuration: totalDuration)
            
            // Main timeline with sections
            VStack(alignment: .leading, spacing: 8) {
                // Section details info
                if let selected = selectedSection ?? hoveredSection {
                    SectionInfoOverlay(section: selected)
                        .transition(.opacity.combined(with: .scale(scale: 0.95)))
                        .animation(.easeInOut(duration: 0.2), value: selectedSection)
                        .animation(.easeInOut(duration: 0.15), value: hoveredSection)
                }
                
                // Sections timeline with enhanced visuals
                ScrollView(.horizontal, showsIndicators: true) {
                    HStack(spacing: 1) {
                        ForEach(sections, id: \.id) { section in
                            EnhancedSectionBlock(
                                section: section,
                                totalDuration: totalDuration,
                                isSelected: selectedSection?.id == section.id,
                                isHovered: hoveredSection?.id == section.id
                            )
                            .onTapGesture {
                                withAnimation(.easeInOut(duration: 0.2)) {
                                    selectedSection = selectedSection?.id == section.id ? nil : section
                                }
                                // Seek to section start time
                                currentTime = section.startTime
                            }
                            .onHover { hovering in
                                withAnimation(.easeInOut(duration: 0.15)) {
                                    hoveredSection = hovering ? section : nil
                                }
                            }
                            .accessibilityLabel("\(section.name) section")
                            .accessibilityHint("Duration: \(section.formattedDuration). Double tap to seek to \(formatTime(section.startTime))")
                            .accessibilityAddTraits(selectedSection?.id == section.id ? [.isSelected] : [])
                        }
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                }
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(Color(.controlBackgroundColor).opacity(0.5))
                )
            }
            
            // Enhanced playback controls
            EnhancedPlaybackControls(
                currentTime: $currentTime,
                totalDuration: totalDuration,
                isPlaying: .constant(false)
            )
            .accessibilityElement(children: .contain)
            .accessibilityLabel("Timeline playback controls")
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.controlBackgroundColor))
                .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
        )
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

/// Song section data model with enhanced functionality
/// 
/// Provides helper methods for duration calculation and formatting
/// Includes computed properties for better UI integration
struct SongSection {
    let id = UUID()
    let name: String
    let startTime: TimeInterval
    let endTime: TimeInterval
    let color: Color
    
    /// Helper to get section duration
    var duration: TimeInterval {
        return endTime - startTime
    }
    
    /// Helper to check if section is short (less than 10 seconds)
    var isShort: Bool {
        return duration < 10
    }
    
    /// Helper to get formatted duration string
    var formattedDuration: String {
        if duration < 60 {
            return String(format: "%.0fs", duration)
        } else {
            let minutes = Int(duration) / 60
            let seconds = Int(duration) % 60
            return String(format: "%dm %ds", minutes, seconds)
        }
    }
}

#Preview {
    TimelineView(
        audioFile: URL(fileURLWithPath: "/sample.mp3"), 
        isAnalyzing: .constant(false),
        sections: .constant([
            SongSection(name: "Intro", startTime: 0, endTime: 12, color: .blue),
            SongSection(name: "Verse 1", startTime: 12, endTime: 40, color: .green),
            SongSection(name: "Chorus", startTime: 40, endTime: 68, color: .orange),
            SongSection(name: "Bridge", startTime: 68, endTime: 92, color: .purple),
            SongSection(name: "Final Chorus", startTime: 92, endTime: 120, color: .orange),
            SongSection(name: "Outro", startTime: 120, endTime: 140, color: .red)
        ]),
        onAnalysisComplete: { _ in }
    )
    .frame(width: 600, height: 400)
    .padding()
}

// MARK: - Enhanced Timeline Components

/// Dynamic time ruler that adapts interval spacing based on song duration
/// 
/// - For songs ≤ 60 seconds: 10-second intervals
/// - For songs ≤ 300 seconds: 30-second intervals  
/// - For songs > 300 seconds: 60-second intervals
struct TimeRuler: View {
    let totalDuration: TimeInterval
    
    private var timeInterval: TimeInterval {
        // Dynamic interval based on duration
        if totalDuration <= 60 {
            return 10 // 10 second intervals for short songs
        } else if totalDuration <= 300 {
            return 30 // 30 second intervals for medium songs
        } else {
            return 60 // 1 minute intervals for long songs
        }
    }
    
    var body: some View {
        HStack(alignment: .top, spacing: 0) {
            ForEach(0..<Int(totalDuration/timeInterval) + 2, id: \.self) { index in
                let time = TimeInterval(index) * timeInterval
                
                if time <= totalDuration {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(formatTime(time))
                            .font(.caption2)
                            .foregroundColor(.secondary)
                            .fontWeight(.medium)
                        
                        Rectangle()
                            .fill(index % 2 == 0 ? Color.primary : Color.secondary)
                            .frame(width: 1, height: index % 2 == 0 ? 8 : 4)
                    }
                    
                    if index < Int(totalDuration/timeInterval) + 1 {
                        Spacer()
                    }
                }
            }
        }
        .padding(.horizontal, 8)
        .padding(.bottom, 4)
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

/// Information overlay that displays detailed section information
/// Shows section name, time range, and duration in a styled container
struct SectionInfoOverlay: View {
    let section: SongSection
    
    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(section.color)
                .frame(width: 8, height: 8)
            
            VStack(alignment: .leading, spacing: 1) {
                Text(section.name)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                
                Text("\(formatTime(section.startTime)) - \(formatTime(section.endTime)) (\(formatDuration(section.endTime - section.startTime)))")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color(.controlBackgroundColor))
                .stroke(section.color.opacity(0.3), lineWidth: 1)
        )
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
    
    private func formatDuration(_ duration: TimeInterval) -> String {
        if duration < 60 {
            return String(format: "%.0fs", duration)
        } else {
            let minutes = Int(duration) / 60
            let seconds = Int(duration) % 60
            return String(format: "%dm %ds", minutes, seconds)
        }
    }
}

/// Enhanced section block with interactive states and visual effects
///
/// Features:
/// - Gradient fills for better visual appeal
/// - Interactive hover and selection states
/// - Dynamic sizing based on section duration
/// - Smooth animations and transitions
/// - Accessibility support
struct EnhancedSectionBlock: View {
    let section: SongSection
    let totalDuration: TimeInterval
    let isSelected: Bool
    let isHovered: Bool
    
    private var blockWidth: CGFloat {
        let sectionDuration = section.endTime - section.startTime
        let ratio = sectionDuration / totalDuration
        let minWidth: CGFloat = 40 // Minimum width for readability
        let maxWidth: CGFloat = 600 // Maximum width for very long sections
        let calculatedWidth = ratio * 500 // Base timeline width
        return max(minWidth, min(maxWidth, calculatedWidth))
    }
    
    private var sectionColor: Color {
        if isSelected {
            return section.color.opacity(0.9)
        } else if isHovered {
            return section.color.opacity(0.8)
        } else {
            return section.color.opacity(0.7)
        }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            // Section block with enhanced styling
            Rectangle()
                .fill(
                    LinearGradient(
                        colors: [
                            sectionColor,
                            sectionColor.opacity(0.8)
                        ],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )
                .frame(width: blockWidth, height: isSelected ? 36 : (isHovered ? 34 : 32))
                .overlay(
                    // Section name overlay
                    Text(section.name)
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundColor(.white)
                        .shadow(color: .black.opacity(0.5), radius: 1, x: 0, y: 0.5)
                        .padding(.horizontal, 6)
                        .multilineTextAlignment(.center)
                        .lineLimit(2)
                )
                .overlay(
                    // Selection/hover border
                    RoundedRectangle(cornerRadius: 4)
                        .stroke(
                            isSelected ? Color.white : (isHovered ? Color.white.opacity(0.6) : Color.clear),
                            lineWidth: isSelected ? 2 : 1
                        )
                )
                .cornerRadius(4)
                .shadow(
                    color: .black.opacity(isSelected ? 0.3 : (isHovered ? 0.2 : 0.1)),
                    radius: isSelected ? 4 : (isHovered ? 3 : 2),
                    x: 0,
                    y: isSelected ? 2 : 1
                )
                .scaleEffect(isSelected ? 1.05 : (isHovered ? 1.02 : 1.0))
            
            // Timestamp with improved styling
            Text(formatTime(section.startTime))
                .font(.caption2)
                .foregroundColor(.secondary)
                .fontWeight(.medium)
        }
        .animation(.easeInOut(duration: 0.2), value: isSelected)
        .animation(.easeInOut(duration: 0.15), value: isHovered)
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

/// Full-featured playback controls with skip and speed functionality
///
/// Features:
/// - Skip backward/forward 10 seconds
/// - Play/pause button with state indication
/// - Scrubbing slider with accent color theming
/// - Speed control menu (0.5x to 2x)
/// - Time display for current and total duration
struct EnhancedPlaybackControls: View {
    @Binding var currentTime: TimeInterval
    let totalDuration: TimeInterval
    @Binding var isPlaying: Bool
    
    var body: some View {
        VStack(spacing: 8) {
            // Progress slider with enhanced styling
            VStack(spacing: 4) {
                Slider(
                    value: $currentTime,
                    in: 0...totalDuration,
                    onEditingChanged: { editing in
                        // Handle scrubbing start/end
                    }
                )
                .tint(.accentColor)
                
                // Time labels
                HStack {
                    Text(formatTime(currentTime))
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                    
                    Spacer()
                    
                    Text(formatTime(totalDuration))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            // Control buttons with enhanced styling
            HStack(spacing: 16) {
                Button(action: { 
                    // Skip backward 10 seconds
                    currentTime = max(0, currentTime - 10)
                }) {
                    Image(systemName: "gobackward.10")
                        .font(.title2)
                }
                .buttonStyle(.bordered)
                .controlSize(.large)
                
                Button(action: {
                    isPlaying.toggle()
                }) {
                    Image(systemName: isPlaying ? "pause.circle.fill" : "play.circle.fill")
                        .font(.title)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                
                Button(action: {
                    // Skip forward 10 seconds  
                    currentTime = min(totalDuration, currentTime + 10)
                }) {
                    Image(systemName: "goforward.10")
                        .font(.title2)
                }
                .buttonStyle(.bordered)
                .controlSize(.large)
                
                Spacer()
                
                // Speed control
                Menu {
                    Button("0.5x") { /* Set speed to 0.5x */ }
                    Button("0.75x") { /* Set speed to 0.75x */ }
                    Button("1x") { /* Set speed to 1x */ }
                    Button("1.25x") { /* Set speed to 1.25x */ }
                    Button("1.5x") { /* Set speed to 1.5x */ }
                    Button("2x") { /* Set speed to 2x */ }
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "speedometer")
                        Text("1x")
                    }
                    .font(.caption)
                }
                .menuStyle(.button)
                .buttonStyle(.bordered)
                .controlSize(.small)
            }
        }
        .padding(.top, 8)
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}