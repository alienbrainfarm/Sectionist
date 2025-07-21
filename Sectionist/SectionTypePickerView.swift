import SwiftUI

/// Quick section type picker for inline editing of section types
/// 
/// Features:
/// - Common section types with appropriate colors
/// - Quick selection without opening full editing interface
/// - Contextual popover that appears on section click
struct SectionTypePickerView: View {
    let currentSection: SongSection
    let onTypeChange: (String, Color) -> Void
    @Environment(\.dismiss) private var dismiss
    
    private let sectionTypes: [SectionType] = [
        SectionType(name: "Intro", color: .blue, icon: "play.circle"),
        SectionType(name: "Verse 1", color: .green, icon: "1.circle"),
        SectionType(name: "Verse 2", color: .green, icon: "2.circle"),
        SectionType(name: "Verse 3", color: .green, icon: "3.circle"),
        SectionType(name: "Chorus", color: .orange, icon: "repeat.circle"),
        SectionType(name: "Pre-Chorus", color: .mint, icon: "arrow.up.circle"),
        SectionType(name: "Bridge", color: .purple, icon: "bridge"),
        SectionType(name: "Solo", color: .yellow, icon: "guitars"),
        SectionType(name: "Breakdown", color: .cyan, icon: "waveform.path.ecg"),
        SectionType(name: "Interlude", color: .indigo, icon: "pause.circle"),
        SectionType(name: "Outro", color: .red, icon: "stop.circle"),
        SectionType(name: "Other", color: .gray, icon: "questionmark.circle")
    ]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HeaderView()
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 8) {
                ForEach(sectionTypes, id: \.name) { sectionType in
                    SectionTypeButton(
                        sectionType: sectionType,
                        isSelected: currentSection.name == sectionType.name,
                        onSelect: {
                            onTypeChange(sectionType.name, sectionType.color)
                            dismiss()
                        }
                    )
                }
            }
            
            CustomSectionInput()
        }
        .padding()
        .frame(width: 300)
        .background(.regularMaterial)
        .cornerRadius(12)
        .shadow(radius: 10)
    }
    
    @ViewBuilder
    private func HeaderView() -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Change Section Type")
                .font(.headline)
                .fontWeight(.semibold)
            
            Text("Currently: \(currentSection.name)")
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
    
    @ViewBuilder
    private func CustomSectionInput() -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Divider()
            
            Text("Custom")
                .font(.subheadline)
                .fontWeight(.medium)
            
            CustomSectionTypeInput(onTypeChange: onTypeChange)
        }
    }
}

/// Individual section type button with icon and color
struct SectionTypeButton: View {
    let sectionType: SectionType
    let isSelected: Bool
    let onSelect: () -> Void
    
    var body: some View {
        Button(action: onSelect) {
            HStack(spacing: 8) {
                Image(systemName: sectionType.icon)
                    .font(.title3)
                    .foregroundColor(sectionType.color)
                    .frame(width: 20)
                
                Text(sectionType.name)
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                
                Spacer()
                
                if isSelected {
                    Image(systemName: "checkmark")
                        .font(.caption)
                        .foregroundColor(.accentColor)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(isSelected ? sectionType.color.opacity(0.15) : Color.clear)
                    .stroke(
                        isSelected ? sectionType.color.opacity(0.5) : Color.clear,
                        lineWidth: 1
                    )
            )
        }
        .buttonStyle(.plain)
        .animation(.easeInOut(duration: 0.2), value: isSelected)
    }
}

/// Custom section type input with color picker
struct CustomSectionTypeInput: View {
    @State private var customName = ""
    @State private var customColor = Color.gray
    @State private var showingColorPicker = false
    let onTypeChange: (String, Color) -> Void
    
    private let quickColors: [Color] = [
        .blue, .green, .orange, .purple, .red, .mint, .cyan, .indigo, .pink, .yellow, .brown, .gray
    ]
    
    var body: some View {
        HStack(spacing: 8) {
            TextField("Section name", text: $customName)
                .textFieldStyle(.roundedBorder)
                .onSubmit {
                    submitCustomSection()
                }
            
            Button(action: { showingColorPicker.toggle() }) {
                Circle()
                    .fill(customColor)
                    .frame(width: 24, height: 24)
                    .overlay(
                        Circle()
                            .stroke(Color.primary.opacity(0.3), lineWidth: 1)
                    )
            }
            .buttonStyle(.plain)
            .popover(isPresented: $showingColorPicker) {
                VStack {
                    Text("Choose Color")
                        .font(.headline)
                        .padding(.top)
                    
                    LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 8) {
                        ForEach(quickColors, id: \.self) { color in
                            Button(action: {
                                customColor = color
                                showingColorPicker = false
                            }) {
                                Circle()
                                    .fill(color)
                                    .frame(width: 30, height: 30)
                                    .overlay(
                                        Circle()
                                            .stroke(
                                                color == customColor ? Color.primary : Color.clear,
                                                lineWidth: 2
                                            )
                                    )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding()
                }
                .frame(width: 200, height: 150)
            }
            
            Button("Add") {
                submitCustomSection()
            }
            .buttonStyle(.bordered)
            .disabled(customName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
        }
    }
    
    private func submitCustomSection() {
        let trimmedName = customName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedName.isEmpty else { return }
        
        onTypeChange(trimmedName, customColor)
        
        // Reset for next use
        customName = ""
        customColor = .gray
    }
}

/// Data model for section types
struct SectionType {
    let name: String
    let color: Color
    let icon: String
}

#Preview {
    SectionTypePickerView(
        currentSection: SongSection(
            name: "Verse 1", 
            startTime: 10, 
            endTime: 40, 
            color: .green
        ),
        onTypeChange: { name, color in
            print("Selected: \(name) with color: \(color)")
        }
    )
}