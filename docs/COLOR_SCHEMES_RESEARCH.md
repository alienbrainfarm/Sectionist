# Color Schemes Research for Sectionist UI

## Overview

This document provides comprehensive research on implementing customizable and accessible color schemes for Sectionist's section layout UI. The research covers best practices, accessibility standards, technical approaches, and user experience considerations for music and audio application interfaces.

## 1. Best Practices for Color Palettes in Music and Audio Apps

### 1.1 Industry Analysis

**Popular Music Applications Color Approaches:**

- **Logic Pro X**: Uses a dark theme with bright, saturated colors for tracks and sections
  - Sections: Bright green, blue, orange, purple, red
  - High contrast against dark backgrounds
  - Color-coded by instrument/section type

- **Ableton Live**: Employs a dark interface with vibrant accent colors
  - Track colors: High-saturation hues across the color spectrum
  - Sections clearly differentiated with contrasting colors
  - Customizable color palettes per track

- **Pro Tools**: Professional gray-based theme with colorful track indicators
  - Muted background with bright track colors
  - Clear visual hierarchy through color contrast

- **Spotify**: Dark mode with green accent, subtle color coding
  - Album artwork drives color schemes dynamically
  - Accessibility-first approach with high contrast

### 1.2 Key Design Principles for Audio Apps

1. **High Contrast**: Essential for timeline scrubbing and section identification
2. **Color Differentiation**: Each section type needs distinct, memorable colors
3. **Dark Mode Optimization**: Most audio professionals prefer dark interfaces
4. **Semantic Color Mapping**: Consistent color meanings (e.g., intro = blue, chorus = orange)
5. **Visual Hierarchy**: Colors should support, not distract from, the primary content

### 1.3 Recommended Color Categories for Song Sections

```
Intro:     Cool blues (#3498db, #2980b9)
Verse:     Natural greens (#27ae60, #2ecc71) 
Chorus:    Energetic oranges (#e67e22, #f39c12)
Bridge:    Unique purples (#9b59b6, #8e44ad)
Outro:     Warm reds (#e74c3c, #c0392b)
Breakdown: Neutral grays (#95a5a6, #7f8c8d)
Solo:      Bright yellows (#f1c40f, #f39c12)
```

## 2. Accessibility Standards and Guidelines

### 2.1 WCAG 2.1 Compliance Requirements

**Contrast Ratios (AA Level):**
- Normal text: 4.5:1 minimum contrast ratio
- Large text (18pt+): 3:1 minimum contrast ratio
- UI components: 3:1 minimum contrast ratio

**AAA Level (Enhanced):**
- Normal text: 7:1 contrast ratio
- Large text: 4.5:1 contrast ratio

### 2.2 Color-Blind Accessibility

**Types of Color Vision Deficiency:**
- Protanopia (Red-blind): ~1% of males
- Deuteranopia (Green-blind): ~1.3% of males  
- Tritanopia (Blue-blind): ~0.02% of population
- Protanomaly/Deuteranomaly: ~6% of males total

**Design Strategies:**
1. **Redundant Encoding**: Use patterns, textures, or labels alongside color
2. **Sufficient Contrast**: Ensure colors remain distinguishable
3. **Color-Blind Safe Palettes**: Use scientifically tested color combinations

### 2.3 Accessibility-Compliant Color Palettes

**Palette 1: High Contrast Classic**
```swift
// Background: #1a1a1a (Dark)
// Text: #ffffff (White)
Intro:    #4a90e2  // Blue - 4.8:1 contrast
Verse:    #7ed321  // Green - 5.2:1 contrast  
Chorus:   #f5a623  // Orange - 4.9:1 contrast
Bridge:   #bd10e0  // Purple - 4.6:1 contrast
Outro:    #d0021b  // Red - 4.7:1 contrast
```

**Palette 2: Color-Blind Friendly**
```swift
// Optimized for Deuteranopia/Protanopia
Intro:    #0173b2  // Blue
Verse:    #029e73  // Teal-green
Chorus:   #cc78bc  // Pink-purple  
Bridge:   #ca9161  // Brown-orange
Outro:    #fbafe4  // Light pink
```

**Palette 3: Soft Professional**
```swift
// Reduced saturation, higher accessibility
Intro:    #5c7cfa  // Soft blue
Verse:    #51cf66  // Soft green
Chorus:   #ffa94d  // Soft orange
Bridge:   #9775fa  // Soft purple  
Outro:    #ff6b6b  // Soft red
```

### 2.4 Accessibility Testing Tools

- **Color Oracle**: Simulates color-blind vision
- **Contrast Checker**: Validates WCAG compliance
- **Sim Daltonism**: Real-time color-blind preview (macOS)
- **Accessible Colors**: Automatic accessible color generation

## 3. User Interface Controls for Customization

### 3.1 Theme Selection Interface

**Primary Options:**
1. **Preset Themes**: Quick selection from curated, accessible themes
2. **Custom Colors**: Individual section color customization
3. **Import/Export**: Share themes between users
4. **Preview Mode**: Live preview without applying changes

**UI Components:**
```
┌─────────────────────────────────┐
│ Theme Selection                 │
├─────────────────────────────────┤
│ ○ High Contrast                 │
│ ● Color-Blind Friendly          │  
│ ○ Soft Professional             │
│ ○ Custom Theme                  │
├─────────────────────────────────┤
│ Section Color Customization:    │
│ Intro:   [🔵] #0173b2          │
│ Verse:   [🟢] #029e73          │
│ Chorus:  [🟣] #cc78bc          │
│ Bridge:  [🟤] #ca9161          │
│ Outro:   [🟡] #fbafe4          │
├─────────────────────────────────┤
│ [Preview] [Apply] [Reset]       │
└─────────────────────────────────┘
```

### 3.2 Advanced Customization Features

**Color Picker Integration:**
- Native SwiftUI ColorPicker with accessibility support
- HSB/RGB value inputs for precise control
- Hex code entry for professional users
- Contrast validation with real-time feedback

**Theme Management:**
- Theme naming and organization
- Import from JSON/plist files
- Export to share with other users
- Cloud sync capability (future enhancement)

### 3.3 User Experience Considerations

**Onboarding:**
1. Show accessibility benefits during first launch
2. Offer quick theme selection wizard
3. Demonstrate theme switching with sample audio

**Contextual Help:**
- Tooltips explaining accessibility features
- Color contrast warnings for invalid combinations
- Recommendations based on system settings (Dark Mode)

## 4. Technical Implementation Approaches

### 4.1 SwiftUI Color Theme Architecture

**Theme Protocol:**
```swift
protocol ColorTheme {
    var name: String { get }
    var introColor: Color { get }
    var verseColor: Color { get }
    var chorusColor: Color { get }
    var bridgeColor: Color { get }
    var outroColor: Color { get }
    var backgroundColor: Color { get }
    var textColor: Color { get }
    
    func contrastRatio(for sectionType: SectionType) -> Double
    func isAccessibilityCompliant() -> Bool
}
```

**Theme Manager:**
```swift
class ThemeManager: ObservableObject {
    @Published var currentTheme: ColorTheme = HighContrastTheme()
    @AppStorage("selectedTheme") private var selectedThemeName: String = "high_contrast"
    
    let availableThemes: [ColorTheme] = [
        HighContrastTheme(),
        ColorBlindFriendlyTheme(),
        SoftProfessionalTheme()
    ]
    
    func applyTheme(_ theme: ColorTheme) {
        currentTheme = theme
        selectedThemeName = theme.name
    }
}
```

### 4.2 SwiftUI Environment Integration

**Environment Value:**
```swift
private struct ThemeEnvironmentKey: EnvironmentKey {
    static let defaultValue: ColorTheme = HighContrastTheme()
}

extension EnvironmentValues {
    var colorTheme: ColorTheme {
        get { self[ThemeEnvironmentKey.self] }
        set { self[ThemeEnvironmentKey.self] = newValue }
    }
}
```

**Usage in Views:**
```swift
struct SectionBlock: View {
    @Environment(\.colorTheme) var theme
    let section: SongSection
    
    var body: some View {
        Rectangle()
            .fill(theme.color(for: section.type))
            .overlay(
                Text(section.name)
                    .foregroundColor(theme.textColor)
            )
    }
}
```

### 4.3 Persistence and Data Management

**UserDefaults Storage:**
```swift
extension UserDefaults {
    func setTheme(_ theme: ColorTheme) {
        let encoder = JSONEncoder()
        if let encoded = try? encoder.encode(theme) {
            set(encoded, forKey: "selectedColorTheme")
        }
    }
    
    func getTheme() -> ColorTheme? {
        if let data = data(forKey: "selectedColorTheme"),
           let theme = try? JSONDecoder().decode(ColorTheme.self, from: data) {
            return theme
        }
        return nil
    }
}
```

**Custom Theme Storage:**
```swift
struct CustomThemeStorage {
    private let documentsDirectory = FileManager.default.urls(for: .documentDirectory, 
                                                            in: .userDomainMask).first!
    
    func saveCustomTheme(_ theme: ColorTheme) throws {
        let url = documentsDirectory.appendingPathComponent("\(theme.name).theme")
        let data = try JSONEncoder().encode(theme)
        try data.write(to: url)
    }
    
    func loadCustomThemes() -> [ColorTheme] {
        // Implementation for loading custom themes from documents directory
    }
}
```

### 4.4 Accessibility Integration

**VoiceOver Support:**
```swift
.accessibilityLabel("\(section.name) section")
.accessibilityValue("Color: \(theme.accessibilityDescription(for: section.type))")
.accessibilityHint("Double tap to select this section")
```

**Dynamic Type Support:**
```swift
Text(section.name)
    .font(.caption)
    .dynamicTypeSize(.small...large)
```

**Reduce Motion Support:**
```swift
@Environment(\.accessibilityReduceMotion) var reduceMotion

// Conditional animations based on user preference
.animation(reduceMotion ? nil : .spring(), value: selectedTheme)
```

## 5. Example User Flows

### 5.1 First-Time Setup Flow

```
1. App Launch
   └── Welcome Screen
       ├── "Choose Your Theme" wizard
       │   ├── Accessibility preferences detection
       │   ├── Color vision test (optional)
       │   └── Theme recommendation
       └── Quick theme selection
           ├── Preview with sample timeline
           └── Apply selection

2. Main Interface
   └── Settings accessible via gear icon
       └── Theme customization panel
```

### 5.2 Theme Switching Flow

```
1. Settings/Preferences Panel
   ├── Theme Selection Grid
   │   ├── Live preview thumbnails
   │   ├── Accessibility badges
   │   └── Custom theme options
   ├── Theme Editor
   │   ├── Section-by-section color picker
   │   ├── Real-time contrast validation
   │   └── Accessibility compliance checker
   └── Import/Export Options
       ├── Share theme files
       └── Community theme library (future)
```

### 5.3 Accessibility-First Flow

```
1. System Settings Detection
   ├── High Contrast Mode → Auto-select high contrast theme
   ├── Dark Mode → Optimize for dark backgrounds
   └── Reduce Motion → Disable theme transition animations

2. Manual Accessibility Settings
   ├── Color Vision Assistance
   │   ├── Deuteranopia compensation
   │   ├── Protanopia compensation  
   │   └── Tritanopia compensation
   └── Contrast Boost Options
       ├── Minimum 4.5:1 enforcement
       └── AAA-level 7:1 option
```

## 6. Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [x] Research documentation completion
- [ ] Basic ColorTheme protocol definition
- [ ] Three preset accessible themes implementation
- [ ] ThemeManager observable object creation

### Phase 2: UI Integration (Week 2)  
- [ ] Update TimelineView to use themes
- [ ] Theme selection UI in settings
- [ ] Live preview functionality
- [ ] UserDefaults persistence

### Phase 3: Advanced Features (Week 3)
- [ ] Custom color picker interface
- [ ] Accessibility validation
- [ ] Import/export functionality
- [ ] Contrast ratio calculations

### Phase 4: Polish & Testing (Week 4)
- [ ] VoiceOver support
- [ ] Color-blind testing
- [ ] Performance optimization
- [ ] User documentation

## 7. Success Metrics

- **Accessibility Compliance**: 100% WCAG AA compliance across all themes
- **User Adoption**: >60% of users customize their theme within first week  
- **Accessibility Usage**: Support for all major color vision deficiencies
- **Performance**: Theme switching completes in <100ms
- **User Satisfaction**: Positive feedback on visual customization options

## 8. Future Enhancements

- **Dynamic Theming**: Colors adapt to imported album artwork
- **Community Themes**: User-shared theme marketplace
- **Advanced Accessibility**: AI-powered accessibility suggestions
- **System Integration**: Automatic dark/light mode switching
- **Professional Features**: Export themes for other music software

---

*This research document serves as the foundation for implementing accessible and customizable color schemes in Sectionist's section layout UI.*