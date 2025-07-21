import SwiftUI

/// Enhanced timeline view for displaying song sections with interactive features
/// 
/// Features:
/// - Interactive section selection and hover effects
/// - Dynamic time rulers based on song duration
/// - Click-to-seek functionality
/// - Responsive section blocks with gradients and animations
/// - Enhanced playback controls with skip and speed options
/// - Section editing and labeling capabilities
/// - Accessibility support with proper labels and hints
struct TimelineView: View {
    let audioFile: URL
    @Binding var isAnalyzing: Bool
    @Binding var sections: [SongSection]
    let onAnalysisComplete: (BackendAnalysisData) -> Void
    
    @State private var totalDuration: TimeInterval = 300 // Will be updated from analysis
    @State private var errorMessage: String?
    @State private var showingError = false
    @State private var selectedSection: SongSection?
    @State private var hoveredSection: SongSection?
    @State private var isEditingMode = false
    @State private var showingSectionEditor = false
    
    @StateObject private var analysisService = AnalysisService.shared
    @StateObject private var audioPlayer = AudioPlayerService.shared
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Enhanced header with duration info and editing controls
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
                
                HStack(spacing: 8) {
                    if !sections.isEmpty && !isAnalyzing {
                        Button("Edit Sections") {
                            showingSectionEditor = true
                        }
                        .buttonStyle(.bordered)
                        
                        Toggle("Edit Mode", isOn: $isEditingMode)
                            .toggleStyle(.switch)
                        
                        Button("Re-analyze") {
                            startAnalysis()
                        }
                        .buttonStyle(.bordered)
                    }
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
            // Load the audio file into the player when the view appears
            audioPlayer.loadAudio(from: audioFile)
        }
        .onChange(of: audioFile) { _, newFile in
            // Automatically start analysis when a new file is loaded
            audioPlayer.loadAudio(from: newFile)
            startAnalysis()
        }
        .alert("Analysis Error", isPresented: $showingError) {
            Button("OK") { }
        } message: {
            Text(errorMessage ?? "An unknown error occurred")
        }
        .sheet(isPresented: $showingSectionEditor) {
            SectionEditingView(sections: $sections, totalDuration: totalDuration)
        }
    }
    
    private func loadMockData() {
        // Enhanced mock data for demonstration with more realistic song structure
        // Breaking up the array creation to help the compiler type-check
        var mockSections: [SongSection] = []
        
        mockSections.append(SongSection(name: "Intro", startTime: 0, endTime: 12, color: .blue, isUserEdited: false))
        mockSections.append(SongSection(name: "Verse 1", startTime: 12, endTime: 40, color: .green, isUserEdited: false))
        mockSections.append(SongSection(name: "Pre-Chorus", startTime: 40, endTime: 52, color: .mint, isUserEdited: false))
        mockSections.append(SongSection(name: "Chorus", startTime: 52, endTime: 80, color: .orange, isUserEdited: false))
        mockSections.append(SongSection(name: "Verse 2", startTime: 80, endTime: 108, color: .green, isUserEdited: false))
        mockSections.append(SongSection(name: "Pre-Chorus", startTime: 108, endTime: 120, color: .mint, isUserEdited: false))
        mockSections.append(SongSection(name: "Chorus", startTime: 120, endTime: 148, color: .orange, isUserEdited: false))
        mockSections.append(SongSection(name: "Bridge", startTime: 148, endTime: 180, color: .purple, isUserEdited: false))
        mockSections.append(SongSection(name: "Final Chorus", startTime: 180, endTime: 220, color: .orange, isUserEdited: false))
        mockSections.append(SongSection(name: "Outro", startTime: 220, endTime: 240, color: .red, isUserEdited: false))
        
        sections = mockSections
        totalDuration = 240
    }
    
    @ViewBuilder
    private func AnalyzingPlaceholder() -> some View {
        VStack(spacing: 20) {
            // Animated progress indicator
            AnimatedProgressIndicator()
            
            AnalyzingStatusText()
            
            // Mock progress sections appearing
            MockProgressSections()
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
    private func AnimatedProgressIndicator() -> some View {
        HStack(spacing: 8) {
            ForEach(0..<3) { index in
                AnimatedDot(index: index, isAnalyzing: isAnalyzing)
            }
        }
    }
    
    @ViewBuilder
    private func AnimatedDot(index: Int, isAnalyzing: Bool) -> some View {
        let animation = Animation.easeInOut(duration: 0.6)
            .repeatForever()
            .delay(Double(index) * 0.2)
        
        Circle()
            .fill(Color.accentColor)
            .frame(width: 8, height: 8)
            .scaleEffect(isAnalyzing ? 1.2 : 0.8)
            .animation(animation, value: isAnalyzing)
    }
    
    @ViewBuilder
    private func AnalyzingStatusText() -> some View {
        VStack(spacing: 8) {
            Text("Analyzing audio structure...")
                .font(.headline)
                .fontWeight(.semibold)
            
            Text("Detecting sections, tempo, and key signature")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
    }
    
    @ViewBuilder
    private func MockProgressSections() -> some View {
        HStack(spacing: 4) {
            ForEach(0..<5) { index in
                MockProgressSection(index: index, isAnalyzing: isAnalyzing)
            }
        }
    }
    
    @ViewBuilder
    private func MockProgressSection(index: Int, isAnalyzing: Bool) -> some View {
        let animation = Animation.easeInOut(duration: 0.8)
            .delay(Double(index) * 0.3)
            .repeatForever()
        
        let progressOverlay = RoundedRectangle(cornerRadius: 3)
            .fill(Color.accentColor.opacity(0.6))
            .scaleEffect(x: index < 3 ? 1.0 : 0.0, anchor: .leading)
            .animation(animation, value: isAnalyzing)
        
        RoundedRectangle(cornerRadius: 3)
            .fill(.secondary.opacity(0.3))
            .frame(width: 40, height: 20)
            .overlay(progressOverlay)
    }
    
    @ViewBuilder
    private func EmptyTimelineView() -> some View {
        VStack(spacing: 20) {
            Image(systemName: "waveform.path")
                .font(.system(size: 48))
                .foregroundColor(Color.accentColor.opacity(0.6))
            
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
            // Use GeometryReader to ensure consistent width calculations
            GeometryReader { geometry in
                let availableWidth = geometry.size.width - 16 // Account for padding
                
                VStack(alignment: .leading, spacing: 12) {
                    // Enhanced time ruler with more granular markers
                    TimeRuler(totalDuration: totalDuration, availableWidth: availableWidth)
                    
                    // Main timeline with sections
                    VStack(alignment: .leading, spacing: 8) {
                        // Section details info
                        if let selected = selectedSection ?? hoveredSection {
                            SectionInfoOverlay(section: selected)
                                .transition(.opacity.combined(with: .scale(scale: 0.95)))
                                .animation(.easeInOut(duration: 0.2), value: selectedSection?.id)
                                .animation(.easeInOut(duration: 0.15), value: hoveredSection?.id)
                        }
                        
                        // Sections timeline with enhanced visuals and proper alignment
                        ScrollView(.horizontal, showsIndicators: true) {
                            ZStack(alignment: .topLeading) {
                                // Background rectangle to establish the timeline width
                                Rectangle()
                                    .fill(Color.clear)
                                    .frame(width: availableWidth, height: 50)
                                
                                // Positioned section blocks
                                ForEach(sections, id: \.id) { section in
                                    EnhancedSectionBlock(
                                        section: section,
                                        totalDuration: totalDuration,
                                        availableWidth: availableWidth,
                                        isSelected: selectedSection?.id == section.id,
                                        isHovered: hoveredSection?.id == section.id,
                                        isEditingMode: isEditingMode
                                    )
                                    .position(
                                        x: sectionXPosition(for: section, availableWidth: availableWidth),
                                        y: 25 // Center vertically in the 50pt height
                                    )
                                    .onTapGesture {
                                        withAnimation(.easeInOut(duration: 0.2)) {
                                            selectedSection = selectedSection?.id == section.id ? nil : section
                                        }
                                        // Seek to section start time
                                        audioPlayer.seek(to: section.startTime)
                                    }
                                    .onHover { hovering in
                                        withAnimation(.easeInOut(duration: 0.15)) {
                                            hoveredSection = hovering ? section : nil
                                        }
                                    }
                                    .contextMenu {
                                        SectionContextMenu(section: section)
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
                        audioPlayer: audioPlayer,
                        totalDuration: totalDuration
                    )
                    .accessibilityElement(children: .contain)
                    .accessibilityLabel("Timeline playback controls")
                }
            }
            .frame(height: 200) // Fixed height to prevent layout issues
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.controlBackgroundColor))
                .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
        )
    }
    
    // Helper function to calculate the X position of a section block
    private func sectionXPosition(for section: SongSection, availableWidth: CGFloat) -> CGFloat {
        let startRatio = section.startTime / totalDuration
        let sectionWidth = sectionWidth(for: section, availableWidth: availableWidth)
        return (startRatio * availableWidth) + (sectionWidth / 2) // Position from center of block
    }
    
    // Helper function to calculate section width consistently
    private func sectionWidth(for section: SongSection, availableWidth: CGFloat) -> CGFloat {
        let sectionDuration = section.endTime - section.startTime
        let ratio = sectionDuration / totalDuration
        let minWidth: CGFloat = 40 // Minimum width for readability
        let calculatedWidth = ratio * availableWidth
        return max(minWidth, calculatedWidth)
    }
    
    @ViewBuilder
    private func SectionContextMenu(section: SongSection) -> some View {
        if isEditingMode {
            Button("Edit Section") {
                selectedSection = section
                showingSectionEditor = true
            }
            
            Button("Duplicate Section") {
                duplicateSection(section)
            }
            
            Divider()
            
            Button("Delete Section") {
                deleteSection(section)
            }
        } else {
            Button("Seek to Start") {
                audioPlayer.seek(to: section.startTime)
            }
            
            Button("Select Section") {
                selectedSection = section
            }
        }
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
    
    // MARK: - Section Editing Methods
    
    private func duplicateSection(_ section: SongSection) {
        let duplicatedSection = SongSection(
            name: "\(section.name) Copy",
            startTime: section.endTime,
            endTime: min(section.endTime + section.duration, totalDuration),
            color: section.color,
            isUserEdited: true
        )
        
        withAnimation(.easeInOut(duration: 0.3)) {
            sections.append(duplicatedSection)
            sections.sort { $0.startTime < $1.startTime }
        }
    }
    
    private func deleteSection(_ section: SongSection) {
        withAnimation(.easeInOut(duration: 0.3)) {
            sections.removeAll { $0.id == section.id }
            if selectedSection?.id == section.id {
                selectedSection = nil
            }
        }
    }
}

/// Song section data model with enhanced functionality
/// 
/// Provides helper methods for duration calculation and formatting
/// Includes computed properties for better UI integration
/// Supports editing and modification for section labeling features
struct SongSection: Identifiable, Equatable {
    let id = UUID()
    let name: String
    let startTime: TimeInterval
    let endTime: TimeInterval
    let color: Color
    
    // Editing state
    let isUserEdited: Bool
    let originalName: String?
    
    // Default initializer
    init(name: String, startTime: TimeInterval, endTime: TimeInterval, color: Color, isUserEdited: Bool = false, originalName: String? = nil) {
        self.name = name
        self.startTime = startTime
        self.endTime = endTime
        self.color = color
        self.isUserEdited = isUserEdited
        self.originalName = originalName
    }
    
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
    
    /// Create an edited copy of this section
    func editedCopy(name: String? = nil, startTime: TimeInterval? = nil, endTime: TimeInterval? = nil, color: Color? = nil) -> SongSection {
        return SongSection(
            name: name ?? self.name,
            startTime: startTime ?? self.startTime,
            endTime: endTime ?? self.endTime,
            color: color ?? self.color,
            isUserEdited: true,
            originalName: self.originalName ?? self.name
        )
    }
    
    // Equatable conformance
    static func == (lhs: SongSection, rhs: SongSection) -> Bool {
        return lhs.id == rhs.id
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
    let availableWidth: CGFloat
    
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
    
    private var timeMarkCount: Int {
        return Int(totalDuration/timeInterval) + 2
    }
    
    var body: some View {
        ZStack(alignment: .topLeading) {
            // Background to establish width
            Rectangle()
                .fill(Color.clear)
                .frame(width: availableWidth, height: 20)
            
            // Positioned time markers
            ForEach(0..<timeMarkCount, id: \.self) { index in
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
                    .position(
                        x: timeXPosition(for: time),
                        y: 10 // Center vertically
                    )
                }
            }
        }
        .padding(.horizontal, 8)
        .padding(.bottom, 4)
    }
    
    // Helper function to calculate X position for time markers
    private func timeXPosition(for time: TimeInterval) -> CGFloat {
        let ratio = time / totalDuration
        return ratio * availableWidth
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
/// - Dynamic sizing based on section duration and available width
/// - Smooth animations and transitions
/// - Editing mode indicators and controls
/// - Accessibility support
struct EnhancedSectionBlock: View {
    let section: SongSection
    let totalDuration: TimeInterval
    let availableWidth: CGFloat
    let isSelected: Bool
    let isHovered: Bool
    let isEditingMode: Bool
    
    private var blockWidth: CGFloat {
        let sectionDuration = section.endTime - section.startTime
        let ratio = sectionDuration / totalDuration
        let minWidth: CGFloat = 40 // Minimum width for readability
        let calculatedWidth = ratio * availableWidth
        return max(minWidth, calculatedWidth)
    }
    
    private var blockHeight: CGFloat {
        if isSelected {
            return 36
        } else if isHovered {
            return 34
        } else {
            return 32
        }
    }
    
    private var borderColor: Color {
        if isEditingMode {
            if isSelected {
                return Color.white
            } else if isHovered {
                return Color.white.opacity(0.6)
            } else {
                return Color.white.opacity(0.3)
            }
        } else {
            if isSelected {
                return Color.white
            } else if isHovered {
                return Color.white.opacity(0.6)
            } else {
                return Color.clear
            }
        }
    }
    
    private var borderLineWidth: CGFloat {
        if isEditingMode {
            return isSelected ? 3 : 2
        } else {
            return isSelected ? 2 : 1
        }
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
                .frame(width: blockWidth, height: blockHeight)
                .overlay(
                    // Section name overlay with edit indicator
                    HStack(spacing: 4) {
                        if section.isUserEdited && isEditingMode {
                            Image(systemName: "pencil.circle.fill")
                                .font(.caption2)
                                .foregroundColor(.white)
                        }
                        
                        Text(section.name)
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(.white)
                            .shadow(color: .black.opacity(0.5), radius: 1, x: 0, y: 0.5)
                            .multilineTextAlignment(.center)
                            .lineLimit(2)
                    }
                    .padding(.horizontal, 6)
                )
                .overlay(
                    // Selection/hover border with editing mode enhancements
                    RoundedRectangle(cornerRadius: 4)
                        .stroke(borderColor, lineWidth: borderLineWidth)
                )
                .overlay(
                    // Editing mode indicators
                    Group {
                        if isEditingMode && (isSelected || isHovered) {
                            VStack {
                                HStack {
                                    // Resize handles
                                    Rectangle()
                                        .fill(Color.white)
                                        .frame(width: 2, height: 16)
                                    Spacer()
                                    Rectangle()
                                        .fill(Color.white)
                                        .frame(width: 2, height: 16)
                                }
                                Spacer()
                            }
                            .padding(2)
                        }
                    }
                )
                .cornerRadius(4)
                .shadow(
                    color: .black.opacity(isSelected ? 0.3 : (isHovered ? 0.2 : 0.1)),
                    radius: isSelected ? 4 : (isHovered ? 3 : 2),
                    x: 0,
                    y: isSelected ? 2 : 1
                )
                .scaleEffect(isSelected ? 1.05 : (isHovered ? 1.02 : 1.0))
            
            // Timestamp with improved styling and edit indicator
            HStack(spacing: 4) {
                Text(formatTime(section.startTime))
                    .font(.caption2)
                    .foregroundColor(.secondary)
                    .fontWeight(.medium)
                
                if section.isUserEdited {
                    Image(systemName: "pencil")
                        .font(.caption2)
                        .foregroundColor(.orange)
                }
            }
        }
        .animation(.easeInOut(duration: 0.2), value: isSelected)
        .animation(.easeInOut(duration: 0.15), value: isHovered)
        .animation(.easeInOut(duration: 0.2), value: isEditingMode)
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
    @ObservedObject var audioPlayer: AudioPlayerService
    let totalDuration: TimeInterval
    
    @State private var isDragging = false
    @State private var draggedTime: TimeInterval = 0
    
    var body: some View {
        VStack(spacing: 8) {
            // Progress slider with enhanced styling
            VStack(spacing: 4) {
                Slider(
                    value: isDragging ? $draggedTime : Binding(
                        get: { audioPlayer.currentTime },
                        set: { audioPlayer.seek(to: $0) }
                    ),
                    in: 0...max(totalDuration, audioPlayer.duration),
                    onEditingChanged: { editing in
                        isDragging = editing
                        if !editing {
                            audioPlayer.seek(to: draggedTime)
                        } else if editing {
                            draggedTime = audioPlayer.currentTime
                        }
                    }
                )
                .tint(Color.accentColor)
                
                // Time labels
                HStack {
                    Text(audioPlayer.formattedCurrentTime)
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                    
                    Spacer()
                    
                    Text(formatTime(max(totalDuration, audioPlayer.duration)))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            // Control buttons with enhanced styling
            HStack(spacing: 16) {
                Button(action: { 
                    audioPlayer.skipBackward()
                }) {
                    Image(systemName: "gobackward.10")
                        .font(.title2)
                }
                .buttonStyle(.bordered)
                .disabled(!audioPlayer.hasAudioLoaded)
                
                Button(action: {
                    audioPlayer.togglePlayback()
                }) {
                    Image(systemName: audioPlayer.isPlaying ? "pause.circle.fill" : "play.circle.fill")
                        .font(.title)
                }
                .buttonStyle(.borderedProminent)
                .disabled(!audioPlayer.hasAudioLoaded)
                
                Button(action: {
                    audioPlayer.skipForward()
                }) {
                    Image(systemName: "goforward.10")
                        .font(.title2)
                }
                .buttonStyle(.bordered)
                .disabled(!audioPlayer.hasAudioLoaded)
                
                Spacer()
                
                // Speed control
                Menu {
                    Button("0.5x") { audioPlayer.setPlaybackRate(0.5) }
                    Button("0.75x") { audioPlayer.setPlaybackRate(0.75) }
                    Button("1x") { audioPlayer.setPlaybackRate(1.0) }
                    Button("1.25x") { audioPlayer.setPlaybackRate(1.25) }
                    Button("1.5x") { audioPlayer.setPlaybackRate(1.5) }
                    Button("2x") { audioPlayer.setPlaybackRate(2.0) }
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "speedometer")
                        Text("\(audioPlayer.playbackRate, specifier: "%.2g")x")
                    }
                    .font(.caption)
                }
                .disabled(!audioPlayer.hasAudioLoaded)
            }
            
            // Error message display
            if let errorMessage = audioPlayer.errorMessage {
                HStack {
                    Image(systemName: "exclamationmark.triangle")
                        .foregroundColor(.orange)
                    Text(errorMessage)
                        .font(.caption)
                        .foregroundColor(.orange)
                    Spacer()
                }
                .padding(.top, 4)
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