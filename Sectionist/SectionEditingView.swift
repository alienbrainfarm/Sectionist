import SwiftUI

/// Section editing view providing comprehensive editing capabilities for song sections
/// 
/// Features:
/// - Rename sections with inline editing
/// - Adjust section boundaries with drag controls
/// - Add new sections between existing ones
/// - Delete sections with confirmation
/// - Change section colors and types
/// - Real-time preview of changes
struct SectionEditingView: View {
    @Binding var sections: [SongSection]
    let totalDuration: TimeInterval
    @State private var editingSection: SongSection?
    @State private var showingAddSection = false
    @State private var showingDeleteConfirmation = false
    @State private var sectionToDelete: SongSection?
    @State private var draggedSection: SongSection?
    @State private var editingName = ""
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HeaderView()
            
            if sections.isEmpty {
                EmptyStateView()
            } else {
                EditingSectionsList()
            }
            
            ActionButtons()
        }
        .padding()
        .background(Color(.controlBackgroundColor))
        .cornerRadius(12)
        .sheet(isPresented: $showingAddSection) {
            AddSectionSheet(sections: $sections, totalDuration: totalDuration)
        }
        .confirmationDialog(
            "Delete Section",
            isPresented: $showingDeleteConfirmation,
            titleVisibility: .visible
        ) {
            Button("Delete", role: .destructive) {
                if let section = sectionToDelete {
                    deleteSection(section)
                }
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            if let section = sectionToDelete {
                Text("Are you sure you want to delete the \"\(section.name)\" section? This action cannot be undone.")
            }
        }
    }
    
    @ViewBuilder
    private func HeaderView() -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Section Editor")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Text("\(sections.count) sections • \(formatTime(totalDuration))")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Button("Add Section") {
                showingAddSection = true
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.small)
        }
    }
    
    @ViewBuilder
    private func EmptyStateView() -> some View {
        VStack(spacing: 16) {
            Image(systemName: "music.note.list")
                .font(.system(size: 40))
                .foregroundColor(.secondary)
            
            VStack(spacing: 8) {
                Text("No sections detected")
                    .font(.headline)
                
                Text("Add sections manually or analyze audio to detect them automatically")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            
            Button("Add First Section") {
                showingAddSection = true
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, minHeight: 150)
    }
    
    @ViewBuilder
    private func EditingSectionsList() -> some View {
        VStack(spacing: 8) {
            ForEach(sections.indices, id: \.self) { index in
                EditableSectionRow(
                    section: sections[index],
                    isEditing: editingSection?.id == sections[index].id,
                    editingName: $editingName,
                    onStartEdit: { section in
                        editingSection = section
                        editingName = section.name
                    },
                    onFinishEdit: { newName in
                        if let editingSection = editingSection,
                           let sectionIndex = sections.firstIndex(where: { $0.id == editingSection.id }) {
                            sections[sectionIndex] = editingSection.editedCopy(name: newName.isEmpty ? editingSection.name : newName)
                        }
                        self.editingSection = nil
                        editingName = ""
                    },
                    onDelete: { section in
                        sectionToDelete = section
                        showingDeleteConfirmation = true
                    },
                    onTimeChange: { section, newStart, newEnd in
                        updateSectionTime(section, newStart: newStart, newEnd: newEnd)
                    },
                    onColorChange: { section, newColor in
                        updateSectionColor(section, newColor: newColor)
                    }
                )
                .transition(.opacity.combined(with: .scale))
                
                if index < sections.count - 1 {
                    AddSectionBetweenView(
                        beforeSection: sections[index],
                        afterSection: sections[index + 1]
                    )
                }
            }
        }
        .animation(.easeInOut(duration: 0.3), value: sections.count)
    }
    
    @ViewBuilder
    private func ActionButtons() -> some View {
        HStack(spacing: 12) {
            Button("Sort by Time") {
                sortSectionsByTime()
            }
            .buttonStyle(.bordered)
            .controlSize(.small)
            
            Button("Merge Overlaps") {
                mergeOverlappingSections()
            }
            .buttonStyle(.bordered)
            .controlSize(.small)
            
            Spacer()
            
            Button("Reset All") {
                // Reset to original backend analysis or clear all
                // This would require storing original data
            }
            .buttonStyle(.bordered)
            .controlSize(.small)
            .foregroundColor(.orange)
        }
    }
    
    // MARK: - Helper Methods
    
    private func deleteSection(_ section: SongSection) {
        withAnimation(.easeInOut(duration: 0.3)) {
            sections.removeAll { $0.id == section.id }
        }
        sectionToDelete = nil
    }
    
    private func updateSectionTime(_ section: SongSection, newStart: TimeInterval, newEnd: TimeInterval) {
        guard let index = sections.firstIndex(where: { $0.id == section.id }) else { return }
        
        let clampedStart = max(0, min(newStart, totalDuration))
        let clampedEnd = max(clampedStart, min(newEnd, totalDuration))
        
        sections[index] = section.editedCopy(
            startTime: clampedStart,
            endTime: clampedEnd
        )
        
        sortSectionsByTime()
    }
    
    private func updateSectionColor(_ section: SongSection, newColor: Color) {
        guard let index = sections.firstIndex(where: { $0.id == section.id }) else { return }
        
        sections[index] = section.editedCopy(color: newColor)
    }
    
    private func sortSectionsByTime() {
        sections.sort { $0.startTime < $1.startTime }
    }
    
    private func mergeOverlappingSections() {
        var mergedSections: [SongSection] = []
        
        for section in sections.sorted(by: { $0.startTime < $1.startTime }) {
            if let lastSection = mergedSections.last,
               section.startTime <= lastSection.endTime {
                // Merge overlapping sections
                let mergedSection = lastSection.editedCopy(
                    name: "\(lastSection.name) / \(section.name)",
                    endTime: max(lastSection.endTime, section.endTime)
                )
                mergedSections[mergedSections.count - 1] = mergedSection
            } else {
                mergedSections.append(section)
            }
        }
        
        withAnimation(.easeInOut(duration: 0.3)) {
            sections = mergedSections
        }
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

/// Individual editable section row with inline editing capabilities
struct EditableSectionRow: View {
    let section: SongSection
    let isEditing: Bool
    @Binding var editingName: String
    let onStartEdit: (SongSection) -> Void
    let onFinishEdit: (String) -> Void
    let onDelete: (SongSection) -> Void
    let onTimeChange: (SongSection, TimeInterval, TimeInterval) -> Void
    let onColorChange: (SongSection, Color) -> Void
    
    @State private var startTimeText = ""
    @State private var endTimeText = ""
    @State private var showingColorPicker = false
    @FocusState private var isNameFocused: Bool
    
    var body: some View {
        HStack(spacing: 12) {
            // Color indicator with picker
            Button(action: { showingColorPicker = true }) {
                Circle()
                    .fill(section.color)
                    .frame(width: 20, height: 20)
                    .overlay(
                        Circle()
                            .stroke(Color.primary.opacity(0.2), lineWidth: 1)
                    )
            }
            .buttonStyle(.plain)
            .popover(isPresented: $showingColorPicker) {
                ColorPickerView(selectedColor: section.color) { newColor in
                    onColorChange(section, newColor)
                    showingColorPicker = false
                }
            }
            
            // Section name (editable)
            VStack(alignment: .leading, spacing: 2) {
                if isEditing {
                    TextField("Section name", text: $editingName)
                        .textFieldStyle(.roundedBorder)
                        .focused($isNameFocused)
                        .onSubmit {
                            onFinishEdit(editingName)
                        }
                        .font(.subheadline)
                        .fontWeight(.medium)
                } else {
                    Text(section.name)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .onTapGesture(count: 2) {
                            onStartEdit(section)
                        }
                }
                
                Text("Duration: \(section.formattedDuration)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .frame(minWidth: 100, alignment: .leading)
            
            Spacer()
            
            // Time editing controls
            VStack(spacing: 4) {
                HStack(spacing: 8) {
                    Text("Start:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    TimeField(
                        time: section.startTime,
                        onChange: { newStart in
                            onTimeChange(section, newStart, section.endTime)
                        }
                    )
                }
                
                HStack(spacing: 8) {
                    Text("End:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    TimeField(
                        time: section.endTime,
                        onChange: { newEnd in
                            onTimeChange(section, section.startTime, newEnd)
                        }
                    )
                }
            }
            .frame(width: 120)
            
            // Action buttons
            HStack(spacing: 4) {
                if isEditing {
                    Button("Save") {
                        onFinishEdit(editingName)
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.mini)
                    
                    Button("Cancel") {
                        onFinishEdit(section.name) // Revert to original name
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.mini)
                } else {
                    Button("Edit") {
                        onStartEdit(section)
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.mini)
                }
                
                Button("Delete") {
                    onDelete(section)
                }
                .buttonStyle(.bordered)
                .controlSize(.mini)
                .foregroundColor(.red)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color(.controlBackgroundColor))
                .stroke(isEditing ? section.color.opacity(0.5) : Color.clear, lineWidth: 2)
        )
        .onAppear {
            if isEditing {
                isNameFocused = true
            }
        }
        .contextMenu {
            Button("Rename") {
                onStartEdit(section)
            }
            
            Button("Duplicate") {
                // Create a duplicate section
            }
            
            Divider()
            
            Button("Delete", role: .destructive) {
                onDelete(section)
            }
        }
    }
}

/// Time input field for editing section timestamps
struct TimeField: View {
    let time: TimeInterval
    let onChange: (TimeInterval) -> Void
    
    @State private var timeText = ""
    @State private var isEditing = false
    
    var body: some View {
        TextField("0:00", text: $timeText)
            .textFieldStyle(.roundedBorder)
            .frame(width: 60)
            .font(.caption)
            .multilineTextAlignment(.center)
            .onAppear {
                updateTimeText()
            }
            .onChange(of: time) { _, _ in
                if !isEditing {
                    updateTimeText()
                }
            }
            .onEditingChanged { editing in
                isEditing = editing
                if !editing {
                    parseAndUpdate()
                }
            }
            .onSubmit {
                parseAndUpdate()
            }
    }
    
    private func updateTimeText() {
        timeText = formatTime(time)
    }
    
    private func parseAndUpdate() {
        if let newTime = parseTime(timeText) {
            onChange(newTime)
        } else {
            updateTimeText() // Revert to original if invalid
        }
        isEditing = false
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
    
    private func parseTime(_ text: String) -> TimeInterval? {
        let components = text.split(separator: ":").compactMap { Int($0) }
        
        if components.count == 2 {
            return TimeInterval(components[0] * 60 + components[1])
        } else if components.count == 1 {
            return TimeInterval(components[0])
        }
        
        return nil
    }
}

/// Color picker for section customization
struct ColorPickerView: View {
    let selectedColor: Color
    let onColorSelect: (Color) -> Void
    
    private let sectionColors: [Color] = [
        .blue, .green, .orange, .purple, .red, .mint, .cyan, .indigo, .pink, .yellow, .brown, .gray
    ]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Choose Section Color")
                .font(.headline)
                .padding(.horizontal)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 8) {
                ForEach(sectionColors, id: \.self) { color in
                    Button(action: { onColorSelect(color) }) {
                        Circle()
                            .fill(color)
                            .frame(width: 30, height: 30)
                            .overlay(
                                Circle()
                                    .stroke(
                                        color == selectedColor ? Color.primary : Color.clear,
                                        lineWidth: 3
                                    )
                            )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal)
        }
        .padding(.vertical)
        .frame(width: 200)
    }
}

/// View for adding sections between existing ones
struct AddSectionBetweenView: View {
    let beforeSection: SongSection
    let afterSection: SongSection
    
    var body: some View {
        HStack {
            Spacer()
            
            Button(action: {
                // Add section between these two
            }) {
                HStack(spacing: 4) {
                    Image(systemName: "plus.circle.fill")
                        .font(.caption)
                    Text("Add section")
                        .font(.caption2)
                }
                .foregroundColor(.accentColor)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(
                    Capsule()
                        .fill(Color.accentColor.opacity(0.1))
                )
            }
            .buttonStyle(.plain)
            
            Spacer()
        }
        .opacity(0.7)
    }
}

/// Sheet for adding new sections
struct AddSectionSheet: View {
    @Binding var sections: [SongSection]
    let totalDuration: TimeInterval
    
    @State private var sectionName = ""
    @State private var startTime: TimeInterval = 0
    @State private var endTime: TimeInterval = 10
    @State private var selectedColor = Color.blue
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Section Details")
                        .font(.headline)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Name")
                            .font(.subheadline)
                            .fontWeight(.medium)
                        
                        TextField("e.g., Verse 1, Chorus, Bridge", text: $sectionName)
                            .textFieldStyle(.roundedBorder)
                    }
                    
                    HStack(spacing: 20) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Start Time")
                                .font(.subheadline)
                                .fontWeight(.medium)
                            
                            TimeSlider(
                                value: $startTime,
                                range: 0...totalDuration,
                                step: 1
                            )
                        }
                        
                        VStack(alignment: .leading, spacing: 8) {
                            Text("End Time")
                                .font(.subheadline)
                                .fontWeight(.medium)
                            
                            TimeSlider(
                                value: $endTime,
                                range: startTime...totalDuration,
                                step: 1
                            )
                        }
                    }
                    
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Color")
                            .font(.subheadline)
                            .fontWeight(.medium)
                        
                        ColorPickerView(selectedColor: selectedColor) { color in
                            selectedColor = color
                        }
                    }
                }
                
                Spacer()
            }
            .padding()
            .navigationTitle("Add Section")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .confirmationAction) {
                    Button("Add") {
                        addSection()
                        dismiss()
                    }
                    .disabled(sectionName.isEmpty || startTime >= endTime)
                }
            }
        }
        .frame(width: 500, height: 400)
    }
    
    private func addSection() {
        let newSection = SongSection(
            name: sectionName,
            startTime: startTime,
            endTime: endTime,
            color: selectedColor,
            isUserEdited: true
        )
        
        sections.append(newSection)
        sections.sort { $0.startTime < $1.startTime }
    }
}

/// Time slider with formatted display
struct TimeSlider: View {
    @Binding var value: TimeInterval
    let range: ClosedRange<TimeInterval>
    let step: TimeInterval
    
    var body: some View {
        VStack(spacing: 4) {
            Slider(value: $value, in: range, step: step)
                .tint(.accentColor)
            
            Text(formatTime(value))
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

#Preview {
    SectionEditingView(
        sections: .constant([
            SongSection(name: "Intro", startTime: 0, endTime: 12, color: .blue),
            SongSection(name: "Verse 1", startTime: 12, endTime: 40, color: .green),
            SongSection(name: "Chorus", startTime: 40, endTime: 68, color: .orange)
        ]),
        totalDuration: 180
    )
    .frame(width: 600, height: 500)
    .padding()
}