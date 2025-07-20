# Sectionist macOS App

This is the SwiftUI macOS application for Sectionist, a music analysis tool that helps musicians analyze songs by splitting audio into meaningful sections, detecting key changes, and mapping basic chords.

## Features

### Current Implementation (Mock/Placeholder)
- Clean SwiftUI interface optimized for macOS
- File picker and drag-and-drop support for audio files
- Timeline view with placeholder song sections
- Analysis results view with placeholder chord and key information
- Responsive layout with proper macOS styling

### Planned Features
- Integration with Python backend for actual music analysis
- Real song structure segmentation (intro, verse, chorus, etc.)
- Key and key change detection
- Basic chord mapping and progression display
- Export functionality for analysis results

## Building the App

### Requirements
- macOS 14.0 or later
- Xcode 15.0 or later
- Swift 5.9 or later

### Build Instructions

1. Open the project in Xcode:
   ```bash
   open Sectionist.xcodeproj
   ```

2. Select the Sectionist scheme and your target device/simulator

3. Build and run the project:
   - Press `⌘R` to build and run
   - Or use menu: Product > Run

### Project Structure

```
Sectionist/
├── SectionistApp.swift          # Main app entry point
├── ContentView.swift            # Main UI with file handling
├── TimelineView.swift           # Timeline visualization
├── AnalysisResultsView.swift    # Analysis results display
├── Assets.xcassets/             # App icons and colors
├── Preview Content/             # SwiftUI preview assets
└── Sectionist.entitlements      # App permissions
```

## App Permissions

The app requests the following permissions:
- **File Access**: To read audio files selected by the user
- **Downloads Folder**: To access commonly used audio file locations
- **Network**: For future backend communication (local Python service)

## Current Limitations

This is a scaffold/foundation implementation with:
- Mock data for timeline sections and analysis results
- No actual audio processing capabilities yet
- File selection works but files aren't processed
- UI is fully functional as a demonstration

## Next Steps

1. Implement actual file loading and validation
2. Create communication layer with Python backend
3. Replace mock data with real analysis results
4. Add export and save functionality
5. Enhance UI based on real use cases

## Contributing

When working on the SwiftUI app:
1. Follow SwiftUI best practices and patterns
2. Maintain consistent styling with macOS design guidelines
3. Keep views modular and reusable
4. Add appropriate error handling for file operations
5. Test on different macOS versions and screen sizes