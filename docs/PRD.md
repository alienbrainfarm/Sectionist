# Product Requirements Document (PRD) — Sectionist

## Overview

**Sectionist** is a macOS application designed for musicians and music learners. It analyzes a song’s audio file and provides a structured overview of the song, automatically segmenting it into sections (e.g., intro, verse, chorus), detecting key changes, and mapping out basic chords. The application leverages a SwiftUI frontend for native Mac experience and a Python backend for music information retrieval (MIR) and machine learning (ML) processing.

---

## Problem Statement

Learning new songs is time-consuming for musicians, especially when breaking down song structure, keys, and chords by ear. Existing tools focus on either transcription or chord recognition, but few offer a comprehensive, easy-to-use solution for mapping out song sections and harmonic structure directly from audio.

---

## Goals

- Provide musicians with a fast, intuitive way to visualize and understand song structure.
- Lower the technical barrier for analyzing audio to extract musical information.
- Enable local, private processing for user data (no cloud uploads).

---

## Features

### MVP (Minimum Viable Product)

1. **Song Section Segmentation**
   - Users can load an audio file (mp3, wav, etc.).
   - The app automatically segments the song into major sections (intro, verse, chorus, bridge, outro, etc.).
   - Visual timeline displaying sections with labels and timestamps.

2. **Key Detection**
   - Display the detected key of the song.
   - Indicate key changes throughout the timeline (if present).

3. **Chord Mapping (Basic)**
   - Map out basic chords for each section or bar.
   - Display chord labels on the timeline.

### Future Enhancements

- **Lyric Extraction**
  - Extract lyrics from vocal audio (using speech-to-text).
- **Export Options**
  - Export structure, chords, and lyrics as PDF, text, or MIDI.
- **Advanced Chord Detection**
  - Support for more complex harmonies and chord extensions.
- **User Annotation**
  - Allow users to manually adjust or annotate detected sections/chords.
- **Integration**
  - Integrate with DAWs or music notation software.

---

## User Stories

1. **As a musician, I want to drop an audio file into Sectionist and quickly see the song structure, so I can start learning the parts faster.**
2. **As a user, I want to see the key and chord changes along the timeline, so I can practice the song accurately.**
3. **As a singer, I want to extract lyrics from a song, so I can rehearse without searching for lyrics online.**
4. **As a teacher, I want to export the analyzed structure for my students.**

---

## Technical Requirements

### Frontend (Python/PyQt6)
- Cross-platform app (Windows, macOS, Linux) with drag-and-drop or file picker for audio.
- Timeline view showing labeled song sections.
- Display of detected key and chords.
- Responsive UI for analysis progress and errors.

### Backend (Python)
- Audio analysis using MIR/ML libraries (e.g., librosa, madmom, Essentia).
- Song segmentation, key detection, chord estimation.
- REST (localhost HTTP) interface for Python frontend to call backend.
- Local inference (no external API calls).

### Data Handling
- All processing is local to the user's machine.
- Support common audio formats: MP3, WAV, AIFF, etc.

---

## Success Metrics

- User can load a song and see section labels in under 30 seconds.
- Section segmentation accuracy: >75% match to human labeling (measured on test set).
- Key detection accuracy: >80% on test set.
- Chord mapping: basic root and quality correct on >70% of bars in pop/rock music.

---

## Milestones & Timeline

### Original Timeline (Completed Ahead of Schedule)

1. **Project Setup & Scaffolding** ✅ **COMPLETED**
   - Repo, SwiftUI/Python folders, initial README, sample audio file(s).

2. **Basic Song Segmentation** ✅ **COMPLETED**
   - Backend prototype for section detection.
   - SwiftUI frontend to visualize segments.

3. **Key & Chord Detection** ✅ **COMPLETED**  
   - Add key and chord estimation to backend.
   - Update UI to display results.

4. **User Experience Polish** 🚧 **IN PROGRESS**
   - Progress indicators, error handling, UI refinement.

5. **Testing & Docs** ✅ **COMPLETED**
   - Test with various genres and files.
   - User guide and FAQ.

6. **Beta Release** 🚀 **READY**

### Current Status (Updated)
The core functionality outlined in this PRD has been successfully implemented ahead of the original timeline. The project now focuses on UI polish, advanced features, and user experience enhancements.

---

## Dependencies & Risks

- Availability of suitable open-source models for segmentation, key, and chord detection.
- Performance on longer or complex songs.
- Handling edge cases (e.g., live recordings, medleys).
- User privacy: ensure no data leaves device.

---

## Out of Scope (for MVP)

- Real-time/live audio analysis.
- Cloud processing.
- Mobile (iOS) version.
- Advanced music theory features (e.g., custom tuning, tempo mapping).

## Project Evolution Note

**Frontend Migration (2024):** The project has migrated from Swift/SwiftUI (macOS-only) to Python/PyQt6 (cross-platform) to support Windows, macOS, and Linux. The Swift implementation has been archived in `Swift-frontend-archived/` for reference. This change enables broader platform support while maintaining the same core functionality.

---

## Appendix

### References

- [librosa](https://librosa.org/)
- [madmom](https://github.com/CPJKU/madmom)
- [Essentia](https://essentia.upf.edu/)
- [OpenAI Whisper](https://github.com/openai/whisper) (for lyrics, future)

---

**Document version:** 1.0  
**Last updated:** 2025-07-20
