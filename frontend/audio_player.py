#!/usr/bin/env python3
"""
Audio Player Module for Sectionist GUI

This module contains the AudioPlayer class that handles 
audio playback using python-vlc.
"""

try:
    import vlc
except ImportError:
    print("python-vlc not found. Install with: pip install python-vlc")
    import sys
    sys.exit(1)

try:
    from mutagen import File as MutagenFile
except ImportError:
    print("mutagen not found. Install with: pip install mutagen")
    import sys
    sys.exit(1)


class AudioPlayer:
    """Audio player using python-vlc for better seeking and position support."""
    
    def __init__(self):
        # Create VLC instance with options for better compatibility
        vlc_args = [
            '--intf', 'dummy',      # No interface
            '--quiet',              # Less verbose output
        ]
        self.vlc_instance = vlc.Instance(vlc_args)
        self.media_player = self.vlc_instance.media_player_new()
        self.is_playing = False
        self.is_paused = False
        self.current_file = None
        self.duration = 0
        self.media = None
        
    def load_file(self, file_path: str) -> bool:
        """Load an audio file."""
        try:
            # Create media object
            self.media = self.vlc_instance.media_new(file_path)
            self.media_player.set_media(self.media)
            self.current_file = file_path
            
            # Parse media to get duration - use synchronous parsing
            self.media.parse_with_options(vlc.MediaParseFlag.local, 5000)  # 5 second timeout
            
            # Get duration in milliseconds, convert to seconds
            duration_ms = self.media.get_duration()
            if duration_ms > 0:
                self.duration = duration_ms / 1000.0
            else:
                # Fallback to mutagen for duration
                try:
                    audio_file = MutagenFile(file_path)
                    if audio_file is not None:
                        self.duration = audio_file.info.length
                    else:
                        self.duration = 0
                except:
                    self.duration = 0
            
            return True
        except Exception as e:
            print(f"Error loading audio file: {e}")
            return False
    
    def play(self):
        """Start or resume playback."""
        if self.current_file:
            if self.is_paused:
                self.media_player.pause()
                self.is_paused = False
            else:
                self.media_player.play()
            self.is_playing = True
    
    def pause(self):
        """Pause playback."""
        if self.is_playing:
            self.media_player.pause()
            self.is_paused = True
            self.is_playing = False
    
    def stop(self):
        """Stop playback."""
        self.media_player.stop()
        self.is_playing = False
        self.is_paused = False
    
    def set_position(self, position: float):
        """Set playback position in seconds."""
        if self.current_file and self.duration > 0:
            # VLC expects position as a ratio between 0.0 and 1.0
            position_ratio = max(0.0, min(1.0, position / self.duration))
            self.media_player.set_position(position_ratio)
    
    def get_position(self) -> float:
        """Get current playback position in seconds."""
        if self.current_file and self.duration > 0:
            # Get position ratio and convert to seconds
            position_ratio = self.media_player.get_position()
            if position_ratio >= 0:  # VLC returns -1 for invalid position
                return position_ratio * self.duration
        return 0.0
    
    def get_duration(self) -> float:
        """Get total duration in seconds."""
        return self.duration