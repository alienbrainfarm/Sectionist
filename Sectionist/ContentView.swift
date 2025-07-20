import SwiftUI

struct ContentView: View {
    @State private var selectedAudioFile: URL?
    @State private var isAnalyzing = false
    
    var body: some View {
        VStack {
            HeaderView()
            
            if let audioFile = selectedAudioFile {
                VStack {
                    AudioFileInfoView(audioFile: audioFile)
                    
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
                AudioFileDropView(selectedAudioFile: $selectedAudioFile)
            }
        }
        .frame(minWidth: 800, minHeight: 600)
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
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Image(systemName: "music.note")
                    .foregroundColor(.blue)
                Text(audioFile.lastPathComponent)
                    .font(.headline)
                Spacer()
                Button("Change File") {
                    // TODO: Implement file change functionality
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
                // TODO: Implement file picker
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(Color.accentColor, style: StrokeStyle(lineWidth: 2, dash: [5]))
        )
        .padding()
        .onDrop(of: [.audio], isTargeted: nil) { providers in
            // TODO: Implement drag and drop functionality
            return false
        }
    }
}

#Preview {
    ContentView()
}