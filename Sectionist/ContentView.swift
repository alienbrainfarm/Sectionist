import SwiftUI
import UniformTypeIdentifiers

import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @StateObject private var themeManager = ThemeManager()
    @State private var selectedAudioFile: URL?
    @State private var isAnalyzing = false
    @State private var isShowingFilePicker = false
    @State private var isShowingThemeSettings = false
    
    var body: some View {
        VStack {
            HeaderView()
            
            if let audioFile = selectedAudioFile {
                VStack {
                    AudioFileInfoView(audioFile: audioFile, isShowingFilePicker: $isShowingFilePicker)
                    
                    Divider()
                        .padding(.vertical)
                    
                    HStack {
                        TimelineView(audioFile: audioFile, isAnalyzing: $isAnalyzing)
                        
                        Divider()
                        
                        AnalysisResultsView(audioFile: audioFile, isAnalyzing: $isAnalyzing)
                    }
                }
                .padding()
            } else {
                AudioFileDropView(selectedAudioFile: $selectedAudioFile, isShowingFilePicker: $isShowingFilePicker)
            }
        }
        .environment(\.colorTheme, themeManager.currentTheme)
        .frame(minWidth: 800, minHeight: 600)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    isShowingThemeSettings = true
                } label: {
                    Image(systemName: "paintbrush.fill")
                        .help("Theme Settings")
                }
            }
        }
        .fileImporter(
            isPresented: $isShowingFilePicker,
            allowedContentTypes: [.audio],
            allowsMultipleSelection: false
        ) { result in
            switch result {
            case .success(let urls):
                if let url = urls.first {
                    selectedAudioFile = url
                }
            case .failure(let error):
                print("File selection failed: \(error.localizedDescription)")
            }
        }
        .sheet(isPresented: $isShowingThemeSettings) {
            ThemeSelectionView()
                .frame(minWidth: 500, minHeight: 400)
        }
    }
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
            }
            
            Text("File: \(audioFile.path)")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.controlBackgroundColor))
        .cornerRadius(8)
    }
}

struct AudioFileDropView: View {
    @Binding var selectedAudioFile: URL?
    @Binding var isShowingFilePicker: Bool
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "music.note.list")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            
            VStack(spacing: 8) {
                Text("Drop an audio file here")
                    .font(.title2)
                    .fontWeight(.medium)
                
                Text("Supports MP3, WAV, AIFF, and other common formats")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            Button("Choose File") {
                isShowingFilePicker = true
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(Color.accentColor, style: StrokeStyle(lineWidth: 2, dash: [5]))
        )
        .padding()
        .onDrop(of: [UTType.audio], isTargeted: nil) { providers in
            guard let provider = providers.first else { return false }
            
            provider.loadItem(forTypeIdentifier: UTType.audio.identifier, options: nil) { (data, error) in
                if let url = data as? URL {
                    DispatchQueue.main.async {
                        selectedAudioFile = url
                    }
                }
            }
            return true
        }
    }
}

#Preview {
    ContentView()
}