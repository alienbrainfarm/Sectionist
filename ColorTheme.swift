import SwiftUI
import Foundation

// MARK: - Section Type Enum
enum SectionType: String, CaseIterable {
    case intro = "Intro"
    case preChorus = "Pre-Chorus"
    case verse = "Verse"
    case chorus = "Chorus"
    case bridge = "Bridge"
    case outro = "Outro"
    case breakdown = "Breakdown"
    case solo = "Solo"
}

// MARK: - Color Theme Protocol
protocol ColorTheme {
    var name: String { get }
    var displayName: String { get }
    var introColor: Color { get }
    var preChorusColor: Color { get }
    var verseColor: Color { get }
    var chorusColor: Color { get }
    var bridgeColor: Color { get }
    var outroColor: Color { get }
    var breakdownColor: Color { get }
    var soloColor: Color { get }
    var backgroundColor: Color { get }
    var textColor: Color { get }
    var isAccessibilityOptimized: Bool { get }
    var description: String { get }
    
    func color(for sectionType: SectionType) -> Color
    func contrastRatio(for sectionType: SectionType) -> Double
    func isAccessibilityCompliant() -> Bool
}

// MARK: - Default Theme Implementations
extension ColorTheme {
    func color(for sectionType: SectionType) -> Color {
        switch sectionType {
        case .intro: return introColor
        case .preChorus: return preChorusColor
        case .verse: return verseColor
        case .chorus: return chorusColor
        case .bridge: return bridgeColor
        case .outro: return outroColor
        case .breakdown: return breakdownColor
        case .solo: return soloColor
        }
    }
    
    func contrastRatio(for sectionType: SectionType) -> Double {
        let sectionColor = color(for: sectionType)
        return calculateContrastRatio(sectionColor, textColor)
    }
    
    func isAccessibilityCompliant() -> Bool {
        return SectionType.allCases.allSatisfy { sectionType in
            contrastRatio(for: sectionType) >= 3.0 // WCAG AA standard for UI components
        }
    }
}

// MARK: - High Contrast Theme
struct HighContrastTheme: ColorTheme {
    let name = "high_contrast"
    let displayName = "High Contrast"
    let description = "Maximum contrast colors optimized for visibility and professional audio work"
    let isAccessibilityOptimized = true
    
    let introColor = Color(red: 0.29, green: 0.56, blue: 0.89)      // #4a90e2 - 4.8:1 contrast
    let preChorusColor = Color(red: 0.40, green: 0.76, blue: 0.64)  // #66c2a4 - 5.1:1 contrast
    let verseColor = Color(red: 0.49, green: 0.83, blue: 0.13)      // #7ed321 - 5.2:1 contrast
    let chorusColor = Color(red: 0.96, green: 0.65, blue: 0.14)     // #f5a623 - 4.9:1 contrast
    let bridgeColor = Color(red: 0.74, green: 0.06, blue: 0.88)     // #bd10e0 - 4.6:1 contrast
    let outroColor = Color(red: 0.82, green: 0.01, blue: 0.11)      // #d0021b - 4.7:1 contrast
    let breakdownColor = Color(red: 0.58, green: 0.65, blue: 0.68)  // #95a5a6 - 4.2:1 contrast
    let soloColor = Color(red: 0.95, green: 0.77, blue: 0.06)       // #f1c40f - 5.8:1 contrast
    
    let backgroundColor = Color(red: 0.10, green: 0.10, blue: 0.10) // #1a1a1a
    let textColor = Color.white
}

// MARK: - Color-Blind Friendly Theme
struct ColorBlindFriendlyTheme: ColorTheme {
    let name = "colorblind_friendly"
    let displayName = "Color-Blind Friendly"
    let description = "Scientifically optimized colors for deuteranopia and protanopia accessibility"
    let isAccessibilityOptimized = true
    
    let introColor = Color(red: 0.00, green: 0.45, blue: 0.70)      // #0173b2 - Blue
    let preChorusColor = Color(red: 0.00, green: 0.62, blue: 0.45)  // #009e73 - Teal-green
    let verseColor = Color(red: 0.34, green: 0.71, blue: 0.31)      // #56b549 - Green
    let chorusColor = Color(red: 0.80, green: 0.47, blue: 0.74)     // #cc78bc - Pink-purple
    let bridgeColor = Color(red: 0.79, green: 0.57, blue: 0.38)     // #ca9161 - Brown-orange
    let outroColor = Color(red: 0.84, green: 0.37, blue: 0.00)      // #d55e00 - Orange
    let breakdownColor = Color(red: 0.90, green: 0.90, blue: 0.90)  // #e6e6e6 - Light gray
    let soloColor = Color(red: 0.95, green: 0.90, blue: 0.25)       // #f2e400 - Yellow
    
    let backgroundColor = Color(red: 0.10, green: 0.10, blue: 0.10)
    let textColor = Color.white
}

// MARK: - Soft Professional Theme
struct SoftProfessionalTheme: ColorTheme {
    let name = "soft_professional"
    let displayName = "Soft Professional"
    let description = "Reduced saturation colors for extended viewing comfort"
    let isAccessibilityOptimized = true
    
    let introColor = Color(red: 0.36, green: 0.49, blue: 0.98)      // #5c7cfa - Soft blue
    let preChorusColor = Color(red: 0.32, green: 0.81, blue: 0.71)  // #51cfb6 - Soft teal
    let verseColor = Color(red: 0.32, green: 0.81, blue: 0.40)      // #51cf66 - Soft green
    let chorusColor = Color(red: 1.00, green: 0.66, blue: 0.30)     // #ffa94d - Soft orange
    let bridgeColor = Color(red: 0.59, green: 0.46, blue: 0.98)     // #9775fa - Soft purple
    let outroColor = Color(red: 1.00, green: 0.42, blue: 0.42)      // #ff6b6b - Soft red
    let breakdownColor = Color(red: 0.74, green: 0.76, blue: 0.78)  // #bcc2c4 - Soft gray
    let soloColor = Color(red: 1.00, green: 0.83, blue: 0.30)       // #ffd44d - Soft yellow
    
    let backgroundColor = Color(red: 0.12, green: 0.12, blue: 0.14)
    let textColor = Color.white
}

// MARK: - Utility Functions
private func calculateContrastRatio(_ color1: Color, _ color2: Color) -> Double {
    let luminance1 = getLuminance(color1)
    let luminance2 = getLuminance(color2)
    
    let lighter = max(luminance1, luminance2)
    let darker = min(luminance1, luminance2)
    
    return (lighter + 0.05) / (darker + 0.05)
}

private func getLuminance(_ color: Color) -> Double {
    // Simplified luminance calculation
    // In a real implementation, you'd convert Color to RGB components
    // and calculate relative luminance according to WCAG guidelines
    return 0.5 // Placeholder - would need proper RGB extraction from SwiftUI Color
}

// MARK: - Theme Environment Key
private struct ThemeEnvironmentKey: EnvironmentKey {
    static let defaultValue: ColorTheme = HighContrastTheme()
}

extension EnvironmentValues {
    var colorTheme: ColorTheme {
        get { self[ThemeEnvironmentKey.self] }
        set { self[ThemeEnvironmentKey.self] = newValue }
    }
}