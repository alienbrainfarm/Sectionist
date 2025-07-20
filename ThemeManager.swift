import SwiftUI
import Combine

// MARK: - Theme Manager
class ThemeManager: ObservableObject {
    @Published var currentTheme: ColorTheme
    @AppStorage("selectedThemeName") private var selectedThemeName: String = "high_contrast"
    
    // Available built-in themes
    let availableThemes: [ColorTheme] = [
        HighContrastTheme(),
        ColorBlindFriendlyTheme(),
        SoftProfessionalTheme()
    ]
    
    init() {
        // Load the saved theme or default to high contrast
        if let savedTheme = availableThemes.first(where: { $0.name == selectedThemeName }) {
            currentTheme = savedTheme
        } else {
            currentTheme = HighContrastTheme()
        }
    }
    
    // Apply a new theme
    func applyTheme(_ theme: ColorTheme) {
        withAnimation(.easeInOut(duration: 0.3)) {
            currentTheme = theme
            selectedThemeName = theme.name
        }
    }
    
    // Get theme by name
    func theme(named name: String) -> ColorTheme? {
        return availableThemes.first { $0.name == name }
    }
    
    // Check if current theme is accessibility compliant
    var isCurrentThemeAccessible: Bool {
        currentTheme.isAccessibilityCompliant()
    }
    
    // Get accessibility badge info
    func accessibilityInfo(for theme: ColorTheme) -> (isCompliant: Bool, description: String) {
        let isCompliant = theme.isAccessibilityCompliant()
        let description = isCompliant ? "WCAG AA Compliant" : "Limited Accessibility"
        return (isCompliant, description)
    }
}

// MARK: - Theme Selection View
struct ThemeSelectionView: View {
    @StateObject private var themeManager = ThemeManager()
    @State private var showingPreview = false
    @State private var previewTheme: ColorTheme?
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Header
            HStack {
                Text("Color Themes")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Spacer()
                
                if themeManager.isCurrentThemeAccessible {
                    Label("Accessible", systemImage: "checkmark.shield.fill")
                        .font(.caption)
                        .foregroundColor(.green)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.green.opacity(0.1))
                        .cornerRadius(4)
                }
            }
            
            // Theme Grid
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 16) {
                ForEach(themeManager.availableThemes, id: \.name) { theme in
                    ThemePreviewCard(
                        theme: theme,
                        isSelected: themeManager.currentTheme.name == theme.name,
                        onSelect: {
                            themeManager.applyTheme(theme)
                        },
                        onPreview: {
                            previewTheme = theme
                            showingPreview = true
                        }
                    )
                }
            }
            
            // Current theme info
            VStack(alignment: .leading, spacing: 8) {
                Text("Current Theme: \(themeManager.currentTheme.displayName)")
                    .font(.headline)
                
                Text(themeManager.currentTheme.description)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
                let accessibilityInfo = themeManager.accessibilityInfo(for: themeManager.currentTheme)
                Label(accessibilityInfo.description, 
                      systemImage: accessibilityInfo.isCompliant ? "checkmark.circle" : "exclamationmark.circle")
                    .font(.caption)
                    .foregroundColor(accessibilityInfo.isCompliant ? .green : .orange)
            }
            .padding()
            .background(Color(.controlBackgroundColor))
            .cornerRadius(8)
        }
        .environmentObject(themeManager)
        .sheet(isPresented: $showingPreview) {
            if let previewTheme = previewTheme {
                ThemePreviewSheet(theme: previewTheme, themeManager: themeManager)
            }
        }
    }
}

// MARK: - Theme Preview Card
struct ThemePreviewCard: View {
    let theme: ColorTheme
    let isSelected: Bool
    let onSelect: () -> Void
    let onPreview: () -> Void
    
    var body: some View {
        VStack(spacing: 12) {
            // Theme name and accessibility badge
            HStack {
                Text(theme.displayName)
                    .font(.headline)
                    .fontWeight(.medium)
                
                Spacer()
                
                if theme.isAccessibilityOptimized {
                    Image(systemName: "checkmark.shield.fill")
                        .font(.caption)
                        .foregroundColor(.green)
                }
            }
            
            // Color preview
            HStack(spacing: 2) {
                Rectangle()
                    .fill(theme.introColor)
                    .frame(height: 20)
                Rectangle()
                    .fill(theme.verseColor)
                    .frame(height: 20)
                Rectangle()
                    .fill(theme.chorusColor)
                    .frame(height: 20)
                Rectangle()
                    .fill(theme.bridgeColor)
                    .frame(height: 20)
                Rectangle()
                    .fill(theme.outroColor)
                    .frame(height: 20)
            }
            .cornerRadius(4)
            
            // Action buttons
            HStack {
                Button("Preview") {
                    onPreview()
                }
                .buttonStyle(.bordered)
                .font(.caption)
                
                Spacer()
                
                Button(isSelected ? "Selected" : "Apply") {
                    if !isSelected {
                        onSelect()
                    }
                }
                .buttonStyle(isSelected ? .borderedProminent : .bordered)
                .font(.caption)
                .disabled(isSelected)
            }
        }
        .padding()
        .background(isSelected ? Color.accentColor.opacity(0.1) : Color(.controlBackgroundColor))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(isSelected ? Color.accentColor : Color.clear, lineWidth: 2)
        )
        .cornerRadius(8)
    }
}

// MARK: - Theme Preview Sheet
struct ThemePreviewSheet: View {
    let theme: ColorTheme
    let themeManager: ThemeManager
    @Environment(\.dismiss) private var dismiss
    
    // Sample data for preview
    private let sampleSections = [
        PreviewSection(name: "Intro", type: .intro, startTime: 0, endTime: 15),
        PreviewSection(name: "Verse 1", type: .verse, startTime: 15, endTime: 45),
        PreviewSection(name: "Chorus", type: .chorus, startTime: 45, endTime: 75),
        PreviewSection(name: "Bridge", type: .bridge, startTime: 75, endTime: 105),
        PreviewSection(name: "Outro", type: .outro, startTime: 105, endTime: 125)
    ]
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Theme info
                VStack(alignment: .leading, spacing: 8) {
                    Text(theme.displayName)
                        .font(.title)
                        .fontWeight(.bold)
                    
                    Text(theme.description)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    if theme.isAccessibilityOptimized {
                        Label("WCAG AA Compliant", systemImage: "checkmark.shield.fill")
                            .font(.caption)
                            .foregroundColor(.green)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                
                Divider()
                
                // Timeline preview
                VStack(alignment: .leading, spacing: 12) {
                    Text("Timeline Preview")
                        .font(.headline)
                    
                    VStack(spacing: 4) {
                        ForEach(sampleSections, id: \.name) { section in
                            HStack {
                                Rectangle()
                                    .fill(theme.color(for: section.type))
                                    .frame(height: 30)
                                    .overlay(
                                        Text(section.name)
                                            .font(.caption)
                                            .fontWeight(.medium)
                                            .foregroundColor(theme.textColor)
                                    )
                                    .cornerRadius(4)
                                
                                Text("\(Int(section.startTime))s")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                    .frame(width: 30)
                            }
                        }
                    }
                }
                
                Spacer()
                
                // Action buttons
                HStack {
                    Button("Cancel") {
                        dismiss()
                    }
                    .buttonStyle(.bordered)
                    
                    Spacer()
                    
                    Button("Apply Theme") {
                        themeManager.applyTheme(theme)
                        dismiss()
                    }
                    .buttonStyle(.borderedProminent)
                }
            }
            .padding()
            .navigationTitle("Theme Preview")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

// MARK: - Preview Section Model
struct PreviewSection {
    let name: String
    let type: SectionType
    let startTime: TimeInterval
    let endTime: TimeInterval
}

// MARK: - Preview
#Preview {
    ThemeSelectionView()
        .frame(width: 500, height: 600)
}