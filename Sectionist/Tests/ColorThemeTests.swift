import XCTest
@testable import Sectionist

// MARK: - Color Theme Tests
class ColorThemeTests: XCTestCase {
    
    func testHighContrastThemeProperties() {
        let theme = HighContrastTheme()
        
        XCTAssertEqual(theme.name, "high_contrast")
        XCTAssertEqual(theme.displayName, "High Contrast")
        XCTAssertTrue(theme.isAccessibilityOptimized)
        XCTAssertTrue(theme.isAccessibilityCompliant())
    }
    
    func testColorBlindFriendlyThemeProperties() {
        let theme = ColorBlindFriendlyTheme()
        
        XCTAssertEqual(theme.name, "colorblind_friendly")
        XCTAssertEqual(theme.displayName, "Color-Blind Friendly")
        XCTAssertTrue(theme.isAccessibilityOptimized)
        XCTAssertTrue(theme.isAccessibilityCompliant())
    }
    
    func testSoftProfessionalThemeProperties() {
        let theme = SoftProfessionalTheme()
        
        XCTAssertEqual(theme.name, "soft_professional")
        XCTAssertEqual(theme.displayName, "Soft Professional")
        XCTAssertTrue(theme.isAccessibilityOptimized)
        XCTAssertTrue(theme.isAccessibilityCompliant())
    }
    
    func testThemeColorMapping() {
        let theme = HighContrastTheme()
        
        // Test that each section type returns a proper color
        XCTAssertNotNil(theme.color(for: .intro))
        XCTAssertNotNil(theme.color(for: .verse))
        XCTAssertNotNil(theme.color(for: .chorus))
        XCTAssertNotNil(theme.color(for: .bridge))
        XCTAssertNotNil(theme.color(for: .outro))
        XCTAssertNotNil(theme.color(for: .preChorus))
        XCTAssertNotNil(theme.color(for: .breakdown))
        XCTAssertNotNil(theme.color(for: .solo))
    }
    
    func testSectionTypesCoverage() {
        // Ensure all section types are handled
        let allSectionTypes = SectionType.allCases
        
        XCTAssertTrue(allSectionTypes.contains(.intro))
        XCTAssertTrue(allSectionTypes.contains(.verse))
        XCTAssertTrue(allSectionTypes.contains(.chorus))
        XCTAssertTrue(allSectionTypes.contains(.bridge))
        XCTAssertTrue(allSectionTypes.contains(.outro))
        XCTAssertTrue(allSectionTypes.contains(.preChorus))
        XCTAssertTrue(allSectionTypes.contains(.breakdown))
        XCTAssertTrue(allSectionTypes.contains(.solo))
    }
    
    func testThemeManagerInitialization() {
        let themeManager = ThemeManager()
        
        // Should start with high contrast theme as default
        XCTAssertEqual(themeManager.currentTheme.name, "high_contrast")
        XCTAssertEqual(themeManager.availableThemes.count, 3)
        XCTAssertTrue(themeManager.isCurrentThemeAccessible)
    }
    
    func testThemeManagerThemeApplication() {
        let themeManager = ThemeManager()
        let newTheme = ColorBlindFriendlyTheme()
        
        // Apply new theme
        themeManager.applyTheme(newTheme)
        
        XCTAssertEqual(themeManager.currentTheme.name, newTheme.name)
        XCTAssertEqual(themeManager.currentTheme.displayName, newTheme.displayName)
    }
    
    func testSongSectionWithTheme() {
        let section = SongSection(
            name: "Test Chorus", 
            startTime: 60, 
            endTime: 90, 
            type: .chorus
        )
        
        XCTAssertEqual(section.name, "Test Chorus")
        XCTAssertEqual(section.startTime, 60)
        XCTAssertEqual(section.endTime, 90)
        XCTAssertEqual(section.type, .chorus)
    }
    
    func testAccessibilityCompliance() {
        let themes: [ColorTheme] = [
            HighContrastTheme(),
            ColorBlindFriendlyTheme(), 
            SoftProfessionalTheme()
        ]
        
        for theme in themes {
            XCTAssertTrue(theme.isAccessibilityCompliant(), 
                         "\(theme.displayName) should be accessibility compliant")
            XCTAssertTrue(theme.isAccessibilityOptimized,
                         "\(theme.displayName) should be accessibility optimized")
        }
    }
}

// MARK: - Theme Manager Tests
class ThemeManagerTests: XCTestCase {
    
    var themeManager: ThemeManager!
    
    override func setUp() {
        super.setUp()
        themeManager = ThemeManager()
    }
    
    override func tearDown() {
        themeManager = nil
        super.tearDown()
    }
    
    func testDefaultThemeSelection() {
        XCTAssertEqual(themeManager.currentTheme.name, "high_contrast")
        XCTAssertTrue(themeManager.isCurrentThemeAccessible)
    }
    
    func testThemeByName() {
        let highContrastTheme = themeManager.theme(named: "high_contrast")
        let colorBlindTheme = themeManager.theme(named: "colorblind_friendly")
        let softTheme = themeManager.theme(named: "soft_professional")
        let nonExistentTheme = themeManager.theme(named: "non_existent")
        
        XCTAssertNotNil(highContrastTheme)
        XCTAssertNotNil(colorBlindTheme)
        XCTAssertNotNil(softTheme)
        XCTAssertNil(nonExistentTheme)
    }
    
    func testAccessibilityInfo() {
        let theme = HighContrastTheme()
        let info = themeManager.accessibilityInfo(for: theme)
        
        XCTAssertTrue(info.isCompliant)
        XCTAssertEqual(info.description, "WCAG AA Compliant")
    }
}