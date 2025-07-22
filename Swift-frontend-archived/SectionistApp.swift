import SwiftUI

@main
struct SectionistApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .windowResizability(.contentMinSize)
        .commands {
            CommandMenu("View") {
                Toggle("Show Analysis Results", isOn: .init(
                    get: { UserDefaults.standard.bool(forKey: "showAnalysisResults") },
                    set: { UserDefaults.standard.set($0, forKey: "showAnalysisResults") }
                ))
                .keyboardShortcut("r", modifiers: [.command])
            }
            
            CommandMenu("Recent Files") {
                RecentFilesMenu()
            }
        }
    }
}

// Recent files menu component
struct RecentFilesMenu: View {
    @State private var recentFiles: [URL] = []
    
    var body: some View {
        Group {
            if recentFiles.isEmpty {
                Text("No recent files")
                    .foregroundColor(.secondary)
            } else {
                ForEach(Array(recentFiles.enumerated()), id: \.element) { index, url in
                    Button(url.lastPathComponent) {
                        // This would need to communicate back to ContentView
                        // For now, it's a placeholder
                    }
                    .keyboardShortcut(KeyEquivalent(Character("\(index + 1)")), modifiers: [.command])
                }
                
                Divider()
                
                Button("Clear Recent Files") {
                    UserDefaults.standard.removeObject(forKey: "RecentAudioFiles")
                    recentFiles.removeAll()
                }
            }
        }
        .onAppear {
            loadRecentFiles()
        }
    }
    
    private func loadRecentFiles() {
        if let urlStrings = UserDefaults.standard.array(forKey: "RecentAudioFiles") as? [String] {
            recentFiles = urlStrings.compactMap { URL(string: $0) }
        }
    }
}