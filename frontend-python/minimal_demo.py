#!/usr/bin/env python3
"""
Sectionist - Minimal Python Frontend Prototype

This is a minimal demonstration of a Python-based frontend for Sectionist
using only the standard library to show the concept. It demonstrates:

1. Basic GUI structure using tkinter (built-in)
2. File selection and drag & drop concepts
3. Backend communication patterns
4. Timeline visualization approach

For a full implementation, see sectionist_gui.py which uses PyQt6.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import sys
from pathlib import Path
from typing import Dict, Optional

# Try to import requests for backend communication
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Note: requests not available. Backend communication will be simulated.")


class MinimalSectionistApp:
    """Minimal Sectionist Python frontend demonstrating the concept."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sectionist - Python Frontend Prototype")
        self.root.geometry("800x600")
        
        self.current_file = None
        self.analysis_results = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Sectionist", font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="Python Frontend Prototype")
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="Audio File", padding="10")
        file_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        self.file_label = ttk.Label(file_frame, text="No file selected")
        self.file_label.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        browse_btn = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        browse_btn.grid(row=1, column=0, padx=(0, 5))
        
        self.clear_btn = ttk.Button(file_frame, text="Clear", command=self.clear_file, state="disabled")
        self.clear_btn.grid(row=1, column=1, sticky=tk.W)
        
        # Analysis controls
        analysis_frame = ttk.Frame(main_frame)
        analysis_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        analysis_frame.columnconfigure(1, weight=1)
        
        self.analyze_btn = ttk.Button(analysis_frame, text="Analyze Audio", 
                                     command=self.analyze_audio, state="disabled")
        self.analyze_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.status_label = ttk.Label(analysis_frame, text="Ready")
        self.status_label.grid(row=0, column=1, sticky=tk.W)
        
        # Progress bar
        self.progress = ttk.Progressbar(analysis_frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Timeline placeholder
        timeline_frame = ttk.LabelFrame(main_frame, text="Timeline", padding="10")
        timeline_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        timeline_frame.columnconfigure(0, weight=1)
        
        self.timeline_canvas = tk.Canvas(timeline_frame, height=80, bg="lightgray")
        self.timeline_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Results area
        results_frame = ttk.LabelFrame(main_frame, text="Analysis Results", padding="10")
        results_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # Results text with scrollbar
        text_frame = ttk.Frame(results_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.results_text = tk.Text(text_frame, wrap=tk.WORD, state="disabled")
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Backend status
        backend_frame = ttk.Frame(main_frame)
        backend_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        self.backend_status = ttk.Label(backend_frame, text="Backend: Checking...", 
                                       foreground="orange")
        self.backend_status.grid(row=0, column=0)
        
        # Check backend status
        self.check_backend_status()
    
    def browse_file(self):
        """Open file dialog to select an audio file."""
        filetypes = [
            ("Audio files", "*.mp3 *.wav *.aiff *.aif *.m4a *.flac *.ogg *.aac"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=filetypes
        )
        
        if file_path:
            self.load_file(file_path)
    
    def load_file(self, file_path: str):
        """Load an audio file."""
        self.current_file = file_path
        filename = Path(file_path).name
        
        self.file_label.config(text=f"File: {filename}")
        self.analyze_btn.config(state="normal")
        self.clear_btn.config(state="normal")
        
        self.status_label.config(text=f"Loaded: {filename}")
        
        # Clear previous results
        self.clear_results()
    
    def clear_file(self):
        """Clear the current file."""
        self.current_file = None
        self.file_label.config(text="No file selected")
        self.analyze_btn.config(state="disabled")
        self.clear_btn.config(state="disabled")
        self.status_label.config(text="Ready")
        
        self.clear_results()
    
    def clear_results(self):
        """Clear analysis results."""
        self.analysis_results = None
        self.results_text.config(state="normal")
        self.results_text.delete(1.0, tk.END)
        self.results_text.config(state="disabled")
        self.timeline_canvas.delete("all")
    
    def check_backend_status(self):
        """Check if the backend server is running."""
        def check():
            if not REQUESTS_AVAILABLE:
                self.backend_status.config(text="Backend: Simulated (requests not available)", 
                                          foreground="blue")
                return
            
            try:
                response = requests.get("http://127.0.0.1:5000/health", timeout=2)
                if response.status_code == 200:
                    self.backend_status.config(text="Backend: Connected ✓", 
                                              foreground="green")
                else:
                    self.backend_status.config(text="Backend: Error", foreground="red")
            except Exception:
                self.backend_status.config(text="Backend: Not running (start with backend/start_server.sh)", 
                                          foreground="red")
        
        # Run in thread to avoid blocking UI
        threading.Thread(target=check, daemon=True).start()
    
    def analyze_audio(self):
        """Analyze the selected audio file."""
        if not self.current_file:
            return
        
        # Show progress
        self.progress.start()
        self.analyze_btn.config(state="disabled")
        self.status_label.config(text="Analyzing...")
        
        def analyze():
            try:
                if REQUESTS_AVAILABLE:
                    # Real backend analysis
                    result = self.analyze_with_backend()
                else:
                    # Simulated analysis
                    result = self.simulate_analysis()
                
                # Update UI in main thread
                self.root.after(0, lambda: self.analysis_complete(result))
                
            except Exception as e:
                self.root.after(0, lambda: self.analysis_error(str(e)))
        
        # Run analysis in background thread
        threading.Thread(target=analyze, daemon=True).start()
    
    def analyze_with_backend(self) -> Dict:
        """Perform real analysis using the backend server."""
        with open(self.current_file, 'rb') as f:
            files = {'audio': f}
            response = requests.post(
                "http://127.0.0.1:5000/analyze", 
                files=files, 
                timeout=60
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Backend error: {response.status_code}")
    
    def simulate_analysis(self) -> Dict:
        """Simulate analysis results for demonstration."""
        import time
        time.sleep(2)  # Simulate analysis time
        
        filename = Path(self.current_file).name
        
        return {
            "success": True,
            "file_name": filename,
            "analysis": {
                "duration": 180.5,
                "tempo": 120.0,
                "key": "C major",
                "beats_detected": 360,
                "sections": [
                    {"name": "Intro", "start": 0.0, "end": 15.0, "confidence": 0.92},
                    {"name": "Verse 1", "start": 15.0, "end": 45.0, "confidence": 0.88},
                    {"name": "Chorus", "start": 45.0, "end": 75.0, "confidence": 0.95},
                    {"name": "Verse 2", "start": 75.0, "end": 105.0, "confidence": 0.87},
                    {"name": "Chorus", "start": 105.0, "end": 135.0, "confidence": 0.94},
                    {"name": "Bridge", "start": 135.0, "end": 165.0, "confidence": 0.83},
                    {"name": "Outro", "start": 165.0, "end": 180.5, "confidence": 0.89},
                ],
                "key_changes": [
                    {"timestamp": 135.0, "from_key": "C major", "to_key": "A minor", "confidence": 0.78}
                ],
                "chords": [
                    {"name": "C", "start": 0.0, "end": 4.0, "confidence": 0.85},
                    {"name": "Am", "start": 4.0, "end": 8.0, "confidence": 0.82},
                    {"name": "F", "start": 8.0, "end": 12.0, "confidence": 0.88},
                    {"name": "G", "start": 12.0, "end": 16.0, "confidence": 0.90},
                ]
            }
        }
    
    def analysis_complete(self, result: Dict):
        """Handle completed analysis."""
        self.progress.stop()
        self.analyze_btn.config(state="normal")
        
        if result.get("success"):
            self.analysis_results = result
            self.display_results(result)
            self.status_label.config(text="Analysis complete!")
        else:
            error_msg = result.get("error", "Unknown error")
            self.analysis_error(error_msg)
    
    def analysis_error(self, error_message: str):
        """Handle analysis error."""
        self.progress.stop()
        self.analyze_btn.config(state="normal")
        self.status_label.config(text=f"Error: {error_message}")
        
        messagebox.showerror("Analysis Error", f"Analysis failed:\n{error_message}")
    
    def display_results(self, result: Dict):
        """Display analysis results."""
        analysis = result.get("analysis", {})
        
        # Build results text
        text = f"Analysis Results for: {result.get('file_name', 'Unknown')}\n"
        text += "=" * 50 + "\n\n"
        
        # Basic info
        text += f"Duration: {self.format_time(analysis.get('duration', 0))}\n"
        text += f"Tempo: {analysis.get('tempo', 0):.1f} BPM\n"
        text += f"Key: {analysis.get('key', 'Unknown')}\n"
        text += f"Beats Detected: {analysis.get('beats_detected', 0)}\n\n"
        
        # Sections
        sections = analysis.get("sections", [])
        if sections:
            text += "Song Sections:\n"
            text += "-" * 20 + "\n"
            for i, section in enumerate(sections, 1):
                name = section.get("name", "Unknown")
                start = section.get("start", 0)
                end = section.get("end", 0)
                confidence = section.get("confidence", 0)
                
                text += f"{i}. {name} ({self.format_time(start)} - {self.format_time(end)}) "
                text += f"[{confidence:.1%}]\n"
            text += "\n"
        
        # Key changes
        key_changes = analysis.get("key_changes", [])
        if key_changes:
            text += "Key Changes:\n"
            text += "-" * 20 + "\n"
            for change in key_changes:
                timestamp = change.get("timestamp", 0)
                from_key = change.get("from_key", "Unknown")
                to_key = change.get("to_key", "Unknown")
                confidence = change.get("confidence", 0)
                
                text += f"At {self.format_time(timestamp)}: {from_key} → {to_key} "
                text += f"[{confidence:.1%}]\n"
            text += "\n"
        
        # Chords
        chords = analysis.get("chords", [])
        if chords:
            text += "Chord Progression (first 10):\n"
            text += "-" * 30 + "\n"
            for chord in chords[:10]:
                name = chord.get("name", "Unknown")
                start = chord.get("start", 0)
                end = chord.get("end", 0)
                confidence = chord.get("confidence", 0)
                
                text += f"{self.format_time(start)}: {name} [{confidence:.1%}]\n"
            
            if len(chords) > 10:
                text += f"... and {len(chords) - 10} more chords\n"
        
        # Display text
        self.results_text.config(state="normal")
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, text)
        self.results_text.config(state="disabled")
        
        # Draw timeline
        self.draw_timeline(sections, analysis.get("duration", 0))
    
    def draw_timeline(self, sections: list, duration: float):
        """Draw a simple timeline visualization."""
        canvas = self.timeline_canvas
        canvas.delete("all")
        
        if not sections or duration <= 0:
            return
        
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        if width <= 1:  # Canvas not initialized yet
            self.root.after(100, lambda: self.draw_timeline(sections, duration))
            return
        
        # Colors for different section types
        colors = {
            "intro": "#4CAF50",     # Green
            "verse": "#2196F3",     # Blue
            "chorus": "#FF9800",    # Orange
            "bridge": "#9C27B0",    # Purple
            "outro": "#F44336",     # Red
        }
        
        # Draw sections
        for section in sections:
            name = section.get("name", "").lower()
            start = section.get("start", 0)
            end = section.get("end", 0)
            
            # Calculate position and width
            x1 = (start / duration) * width
            x2 = (end / duration) * width
            
            # Choose color
            color = "#9E9E9E"  # Default gray
            for key, c in colors.items():
                if key in name:
                    color = c
                    break
            
            # Draw rectangle
            canvas.create_rectangle(x1, 10, x2, height - 10, 
                                   fill=color, outline="black", width=1)
            
            # Draw label if there's space
            if x2 - x1 > 30:
                text_x = (x1 + x2) / 2
                canvas.create_text(text_x, height / 2, text=section.get("name", ""), 
                                 font=("Arial", 8), fill="white")
        
        # Draw time markers
        for i in range(0, int(duration) + 1, 30):  # Every 30 seconds
            x = (i / duration) * width
            canvas.create_line(x, 0, x, height, fill="gray", dash=(2, 2))
            canvas.create_text(x, 5, text=self.format_time(i), 
                              font=("Arial", 7), anchor="n")
    
    def format_time(self, seconds: float) -> str:
        """Format time in MM:SS format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def run(self):
        """Run the application."""
        self.root.mainloop()


def main():
    """Main entry point."""
    print("Sectionist Python Frontend Prototype")
    print("=====================================")
    print()
    print("This is a minimal demonstration of a Python-based frontend")
    print("for Sectionist using tkinter (built-in GUI toolkit).")
    print()
    print("Features demonstrated:")
    print("• File selection and loading")
    print("• Backend communication (or simulation)")
    print("• Analysis results display")
    print("• Timeline visualization")
    print()
    print("For a full-featured version, see sectionist_gui.py (PyQt6).")
    print()
    
    # Check if backend is running
    if REQUESTS_AVAILABLE:
        try:
            import requests
            response = requests.get("http://127.0.0.1:5000/health", timeout=2)
            if response.status_code == 200:
                print("✓ Backend server detected - will use real analysis")
            else:
                print("⚠ Backend server error - will use simulated analysis")
        except Exception:
            print("⚠ Backend server not running - will use simulated analysis")
            print("  To start backend: cd backend && ./start_server.sh")
    else:
        print("⚠ 'requests' library not available - will use simulated analysis")
    
    print()
    print("Starting GUI...")
    
    app = MinimalSectionistApp()
    app.run()


if __name__ == "__main__":
    main()