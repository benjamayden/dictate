#!/usr/bin/env python3
"""
Audio Recording Module

High-quality native audio recording with real-time feedback and auto-save protection.
"""

import threading
import time
import os
import numpy as np
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import json


class MicrophoneManager:
    """Microphone auto-selection and preference persistence.

    Notes:
    - Prefers last-used mic when available
    - Otherwise scores external/pro brands higher and selects highest score
    - Preferences stored at ~/.dictate_preferences.json
    """

    def __init__(self):
        self.preferences_path = Path.home() / ".dictate_preferences.json"

    def load_preferences(self) -> Dict[str, Any]:
        """Load saved microphone preferences."""
        if self.preferences_path.exists():
            try:
                with open(self.preferences_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def save_preferences(self, preferences: Dict[str, Any]) -> None:
        """Save microphone preferences."""
        try:
            with open(self.preferences_path, 'w') as f:
                json.dump(preferences, f, indent=2)
        except IOError:
            pass  # Silently fail if we can't save preferences

    def list_microphones(self) -> List[Dict[str, Any]]:
        """Get a list of available microphones with detailed information."""
        devices = sd.query_devices()
        microphones = []
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                microphones.append({
                    'index': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate'],
                    'hostapi': sd.query_hostapis(device['hostapi'])['name']
                })
        
        return microphones

    def score_microphone(self, device: Dict[str, Any]) -> float:
        """Score a microphone based on quality indicators."""
        score = 0.0
        name = device['name'].lower()
        
        # Prefer external/professional microphones
        if any(brand in name for brand in ['blue', 'rode', 'audio-technica', 'shure', 'zoom']):
            score += 3.0
        elif any(term in name for term in ['usb', 'external']):
            score += 2.0
        elif any(term in name for term in ['built-in', 'internal']):
            score -= 1.0
            
        # Prefer higher channel count
        score += device['channels'] * 0.5
        
        # Prefer higher sample rates
        if device['sample_rate'] >= 44100:
            score += 1.0
            
        return score

    def select_best_microphone(self, preferred_index: Optional[int] = None) -> Optional[int]:
        """Select the best available microphone."""
        microphones = self.list_microphones()
        
        if not microphones:
            return None
            
        # Use preferred index if valid and available
        if preferred_index is not None:
            for mic in microphones:
                if mic['index'] == preferred_index:
                    return preferred_index
                    
        # Check saved preferences
        preferences = self.load_preferences()
        last_used = preferences.get('last_used_microphone')
        if last_used is not None:
            for mic in microphones:
                if mic['index'] == last_used:
                    return last_used
                    
        # Score and select best microphone
        best_mic = max(microphones, key=self.score_microphone)
        return best_mic['index']


class AudioRecorder:
    """High-quality native audio recording with real-time feedback and auto-save protection."""
    
    def __init__(self, sample_rate: int = 44100, channels: int = 1):
        """Initialize the audio recorder.
        
        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels (1 for mono, 2 for stereo)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.frames = []
        self.is_recording = False
        self.auto_save_interval = 10  # Save every 10 seconds
        self.current_file = None
        self.mic_manager = MicrophoneManager()
        self.auto_save_thread = None
        self.temp_file_path = None
        
    def get_available_microphones(self) -> List[Dict[str, Any]]:
        """Get list of available microphones."""
        return self.mic_manager.list_microphones()
        
    def select_microphone(self, preferred_index: Optional[int] = None) -> int:
        """Select the best available microphone."""
        selected = self.mic_manager.select_best_microphone(preferred_index)
        if selected is None:
            raise RuntimeError("No microphones available")
        return selected
        
    def start_recording(self, microphone_index: Optional[int] = None) -> None:
        """Start recording with visual feedback and auto-save protection.
        
        Args:
            microphone_index: Specific microphone to use, or None for auto-selection
        """
        if self.is_recording:
            raise RuntimeError("Already recording")
            
        # Select microphone
        if microphone_index is None:
            microphone_index = self.select_microphone()
            
        # Initialize recording state
        self.frames = []
        self.is_recording = True
        
        # Set up temporary file for auto-save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.temp_file_path = f"temp_recording_{timestamp}.wav"
        
        # Start auto-save thread
        self.auto_save_thread = threading.Thread(target=self._auto_save_worker, daemon=True)
        self.auto_save_thread.start()
        
        # Start recording stream
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio status: {status}")
            if self.is_recording:
                self.frames.append(indata.copy())
                
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            device=microphone_index,
            callback=audio_callback,
            dtype=np.float32
        )
        
        self.stream.start()
        
    def _auto_save_worker(self) -> None:
        """Background thread that saves audio every 10 seconds."""
        while self.is_recording:
            time.sleep(self.auto_save_interval)
            if self.is_recording and self.frames:
                self._save_current_buffer_to_temp()
                
    def _save_current_buffer_to_temp(self) -> None:
        """Save current audio buffer to temporary file."""
        if not self.frames:
            return
            
        try:
            audio_data = np.concatenate(self.frames, axis=0)
            sf.write(self.temp_file_path, audio_data, self.sample_rate)
        except Exception as e:
            print(f"Auto-save failed: {e}")
            
    def stop_recording(self, filename: Optional[str] = None) -> str:
        """Stop recording and save final recording.
        
        Args:
            filename: Custom filename for the recording
            
        Returns:
            Path to the saved recording file
        """
        if not self.is_recording:
            raise RuntimeError("Not currently recording")
            
        self.is_recording = False
        
        # Stop the stream
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
            
        # Wait for auto-save thread to finish
        if self.auto_save_thread and self.auto_save_thread.is_alive():
            self.auto_save_thread.join(timeout=2.0)
            
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
            
        # Ensure .wav extension
        if not filename.endswith('.wav'):
            filename += '.wav'
            
        # Save final recording
        if self.frames:
            audio_data = np.concatenate(self.frames, axis=0)
            sf.write(filename, audio_data, self.sample_rate)
            
            # Save microphone preference
            if hasattr(self, 'stream') and self.stream.device is not None:
                preferences = self.mic_manager.load_preferences()
                preferences['last_used_microphone'] = self.stream.device
                self.mic_manager.save_preferences(preferences)
        else:
            # No audio recorded, create empty file
            sf.write(filename, np.array([[0.0]], dtype=np.float32), self.sample_rate)
            
        # Clean up temporary file
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.remove(self.temp_file_path)
            except OSError:
                pass
                
        return filename
        
    def get_recording_duration(self) -> float:
        """Get current recording duration in seconds."""
        if not self.frames:
            return 0.0
        total_frames = sum(len(frame) for frame in self.frames)
        return total_frames / self.sample_rate
        
    def get_audio_level(self) -> float:
        """Get current audio level (0.0 to 1.0)."""
        if not self.frames or not self.frames[-1].size:
            return 0.0
        recent_data = self.frames[-1]
        return float(np.sqrt(np.mean(recent_data ** 2)))
        
    def emergency_cleanup(self) -> Optional[str]:
        """Handle unexpected termination - recovers last auto-save.
        
        Returns:
            Path to recovered file if available, None otherwise
        """
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            recovered_file = f"recovered_recording_{timestamp}.wav"
            try:
                os.rename(self.temp_file_path, recovered_file)
                return recovered_file
            except OSError:
                pass
        return None
        
    @staticmethod
    def list_temp_files() -> List[str]:
        """List any temporary recording files that can be recovered."""
        temp_files = []
        for file in os.listdir('.'):
            if file.startswith('temp_recording_') and file.endswith('.wav'):
                temp_files.append(file)
        return temp_files
        
    @staticmethod
    def recover_temp_file(temp_file: str, new_name: Optional[str] = None) -> str:
        """Recover a temporary recording file.
        
        Args:
            temp_file: Path to temporary file
            new_name: New name for recovered file
            
        Returns:
            Path to recovered file
        """
        if new_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"recovered_recording_{timestamp}.wav"
            
        os.rename(temp_file, new_name)
        return new_name
