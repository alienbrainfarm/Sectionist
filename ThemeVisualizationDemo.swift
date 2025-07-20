import SwiftUI

// MARK: - Demo View for Theme Visualization
struct ThemeVisualizationDemo: View {
    @StateObject private var themeManager = ThemeManager()
    
    private let sampleSections = [
        SongSection(name: "Intro", startTime: 0, endTime: 15, type: .intro),
        SongSection(name: "Pre-Chorus", startTime: 15, endTime: 30, type: .preChorus),
        SongSection(name: "Verse", startTime: 30, endTime: 60, type: .verse),
        SongSection(name: "Chorus", startTime: 60, endTime: 90, type: .chorus),
        SongSection(name: "Bridge", startTime: 90, endTime: 120, type: .bridge),
        SongSection(name: "Outro", startTime: 120, endTime: 140, type: .outro)
    ]
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Sectionist Color Theme Demonstration")
                .font(.title)
                .fontWeight(.bold)
            
            // Theme selector
            HStack {
                Text("Current Theme:")
                    .font(.headline)
                
                Picker("Theme", selection: Binding(
                    get: { themeManager.currentTheme.name },
                    set: { newThemeName in
                        if let theme = themeManager.theme(named: newThemeName) {
                            themeManager.applyTheme(theme)
                        }
                    }
                )) {
                    ForEach(themeManager.availableThemes, id: \.name) { theme in
                        Text(theme.displayName).tag(theme.name)
                    }
                }
                .pickerStyle(SegmentedPickerStyle())
            }
            
            // Accessibility badge
            if themeManager.isCurrentThemeAccessible {
                Label("WCAG AA Compliant", systemImage: "checkmark.shield.fill")
                    .foregroundColor(.green)
                    .font(.caption)
            }
            
            // Timeline visualization
            VStack(alignment: .leading, spacing: 8) {
                Text("Section Timeline Preview")
                    .font(.headline)
                
                VStack(spacing: 4) {
                    ForEach(sampleSections, id: \.id) { section in
                        HStack {
                            Rectangle()
                                .fill(themeManager.currentTheme.color(for: section.type))
                                .frame(height: 40)
                                .overlay(
                                    HStack {
                                        Text(section.name)
                                            .font(.caption)
                                            .fontWeight(.semibold)
                                            .foregroundColor(themeManager.currentTheme.textColor)
                                        Spacer()
                                        Text("\(Int(section.startTime))s-\(Int(section.endTime))s")
                                            .font(.caption2)
                                            .foregroundColor(themeManager.currentTheme.textColor.opacity(0.8))
                                    }
                                    .padding(.horizontal, 8)
                                )
                                .cornerRadius(6)
                            
                            // Color hex display
                            Text(colorToHex(themeManager.currentTheme.color(for: section.type)))
                                .font(.caption2)
                                .foregroundColor(.secondary)
                                .frame(width: 80)
                        }
                    }
                }
                .padding()
                .background(themeManager.currentTheme.backgroundColor)
                .cornerRadius(12)
            }
            
            // Theme information
            VStack(alignment: .leading, spacing: 8) {
                Text("Theme Information")
                    .font(.headline)
                
                Text(themeManager.currentTheme.description)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
                if themeManager.currentTheme.isAccessibilityOptimized {
                    Label("Accessibility Optimized", systemImage: "eye.fill")
                        .font(.caption)
                        .foregroundColor(.blue)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            .background(Color(.controlBackgroundColor))
            .cornerRadius(8)
            
            Spacer()
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(themeManager.currentTheme.backgroundColor.opacity(0.1))
    }
    
    private func colorToHex(_ color: Color) -> String {
        // Simplified hex conversion - in real implementation would use proper Color to hex conversion
        let colors: [String: String] = [
            "intro": "#4a90e2",
            "verse": "#7ed321", 
            "chorus": "#f5a623",
            "bridge": "#bd10e0",
            "outro": "#d0021b",
            "preChorus": "#66c2a4"
        ]
        return colors["intro"] ?? "#000000" // Placeholder
    }
}

// MARK: - Preview
#Preview("High Contrast Theme") {
    ThemeVisualizationDemo()
        .frame(width: 800, height: 600)
}

#Preview("Color-Blind Friendly Theme") {
    let demo = ThemeVisualizationDemo()
    return demo
        .frame(width: 800, height: 600)
        .onAppear {
            demo.themeManager.applyTheme(ColorBlindFriendlyTheme())
        }
}

#Preview("Soft Professional Theme") {
    let demo = ThemeVisualizationDemo()
    return demo
        .frame(width: 800, height: 600)
        .onAppear {
            demo.themeManager.applyTheme(SoftProfessionalTheme())
        }
}