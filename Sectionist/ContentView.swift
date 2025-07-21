import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @State private var selectedAudioFile: URL?
    @State private var isAnalyzing = false
    @State private var isShowingFilePicker = false
    @State private var errorMessage: String?
    @State private var showingError = false
    
    // Shared analysis state
    @State private var analysisResults: AnalysisData?
    @State private var songSections: [SongSection] = []
    
    var body: some View {
        VStack {
            HeaderView()
            
                if let audioFile = selectedAudioFile {
                VStack {
                    AudioFileInfoView(
                        audioFile: audioFile, 
                        isShowingFilePicker: $isShowingFilePicker,
                        onClear: {
                            selectedAudioFile = nil
                            isAnalyzing = false
                            analysisResults = nil
                            songSections = []
                        }
                    )
                    
                    Divider()
                        .padding(.vertical)
                    
                    HStack {
                        TimelineView(
                            audioFile: audioFile, 
                            isAnalyzing: $isAnalyzing, 
                            sections: $songSections,
                            onAnalysisComplete: handleAnalysisComplete
                        )
                        
                        Divider()
                        
                        AnalysisResultsView(
                            audioFile: audioFile, 
                            isAnalyzing: $isAnalyzing, 
                            analysisResults: $analysisResults
                        )
                    }
                }
                .padding()
            } else {
                AudioFileDropView(selectedAudioFile: $selectedAudioFile, isShowingFilePicker: $isShowingFilePicker)
            }
        }
        .frame(minWidth: 800, minHeight: 600)
        .fileImporter(
            isPresented: $isShowingFilePicker,
            allowedContentTypes: [.audio],
            allowsMultipleSelection: false
        ) { result in
            switch result {
            case .success(let urls):
                if let url = urls.first {
                    // Start accessing security-scoped resource for sandboxed app
                    _ = url.startAccessingSecurityScopedResource()
                    selectedAudioFile = url
                }
            case .failure(let error):
                errorMessage = "File selection failed: \(error.localizedDescription)"
                showingError = true
            }
        }
        .alert("Error", isPresented: $showingError) {
            Button("OK") { }
        } message: {
            Text(errorMessage ?? "An unknown error occurred")
        }
    }
    
    private func handleAnalysisComplete(backendData: BackendAnalysisData) {
        // Update both timeline and analysis results with the same data
        songSections = backendData.toSongSections()
        analysisResults = backendData.toAnalysisData()
    }
}

struct HeaderView: View {
    var body: some View {
        VStack {
            Text("Sectionist")
                .font(.largeTitle)
                .fontWeight(.bold)
                .padding(.top)
            
            Text("Analyze your songs • Visualize structure • Understand harmony")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .padding(.bottom)
        }
    }
}

struct AudioFileInfoView: View {
    let audioFile: URL
    @Binding var isShowingFilePicker: Bool
    let onClear: () -> Void
    @State private var showingClearConfirmation = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Image(systemName: "music.note")
                    .foregroundColor(.blue)
                Text(audioFile.lastPathComponent)
                    .font(.headline)
                Spacer()
                
                Button("Change File") {
                    isShowingFilePicker = true
                }
                .buttonStyle(.bordered)
                
                Button("Clear") {
                    showingClearConfirmation = true
                }
                .buttonStyle(.bordered)
                .foregroundColor(.red)
            }
            
            Text("File: \(audioFile.path)")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.controlBackgroundColor))
        .cornerRadius(8)
        .confirmationDialog("Clear current file?", isPresented: $showingClearConfirmation) {
            Button("Clear", role: .destructive) {
                onClear()
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("This will remove the current audio file and analysis.")
        }
    }
}

struct AudioFileDropView: View {
    @Binding var selectedAudioFile: URL?
    @Binding var isShowingFilePicker: Bool
    @State private var isTargeted = false
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "music.note.list")
                .font(.system(size: 60))
                .foregroundColor(isTargeted ? .accentColor : .secondary)
                .animation(.easeInOut(duration: 0.2), value: isTargeted)
            
            VStack(spacing: 8) {
                Text("Drop an audio file here")
                    .font(.title2)
                    .fontWeight(.medium)
                
                Text("Supports MP3, WAV, AIFF, M4A, FLAC and other common formats")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                
                // Visual file type indicators
                HStack(spacing: 8) {
                    ForEach(["MP3", "WAV", "M4A", "FLAC"], id: \.self) { format in
                        Text(format)
                            .font(.caption2)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(Color.accentColor.opacity(0.1))
                            .foregroundColor(.accentColor)
                            .cornerRadius(4)
                    }
                }
                .padding(.top, 4)
            }
            
            Button("Choose File") {
                isShowingFilePicker = true
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(
                    isTargeted ? Color.accentColor : Color.accentColor.opacity(0.5),
                    style: StrokeStyle(lineWidth: isTargeted ? 3 : 2, dash: [5])
                )
                .animation(.easeInOut(duration: 0.2), value: isTargeted)
        )
        .padding()
        .onDrop(of: [UTType.fileURL, UTType.audio], isTargeted: $isTargeted) { providers in
            handleDrop(providers: providers)
        }
    }
    
    private func handleDrop(providers: [NSItemProvider]) -> Bool {
        guard let provider = providers.first else { return false }
        
        // Try to handle as file URL first (most common case)
        if provider.hasItemConformingToTypeIdentifier(UTType.fileURL.identifier) {
            provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { (urlData, error) in
                DispatchQueue.main.async {
                    if let error = error {
                        print("Error loading dropped file: \(error.localizedDescription)")
                        return
                    }
                    
                    guard let urlData = urlData as? Data,
                          let urlString = String(data: urlData, encoding: .utf8),
                          let url = URL(string: urlString) else {
                        print("Could not parse dropped file URL")
                        return
                    }
                    
                    if isValidAudioFile(url) {
                        _ = url.startAccessingSecurityScopedResource()
                        selectedAudioFile = url
                    } else {
                        print("Dropped file is not a supported audio format: \(url.pathExtension)")
                    }
                }
            }
            return true
        }
        
        return false
    }
    
    private func isValidAudioFile(_ url: URL) -> Bool {
        let audioExtensions = ["mp3", "wav", "aiff", "aif", "m4a", "flac", "ogg", "wma", "aac", "opus"]
        return audioExtensions.contains(url.pathExtension.lowercased())
    }
}

#Preview {
    ContentView()
}