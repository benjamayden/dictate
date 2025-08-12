#!/usr/bin/env python3
"""
Voice Dictation Tool

A simple script to record audio, transcribe it using Gemini, and save both
the audio file and formatted transcript.

Usage:
    python3 dictate.py
    
Requirements:
    pip install sounddevice soundfile google-generativeai numpy python-dotenv

Setup:
    1. Copy CONFIGURATION_TEMPLATE.txt to .env
    2. Update .env with your API key and preferred settings
"""

import os
import sys
import time
import datetime
import numpy as np
import sounddevice as sd
import soundfile as sf
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_base_directory():
    """Get the base directory for recordings from environment or use default"""
    # Check if custom directory is set in environment
    custom_dir = os.getenv('DICTATE_RECORDINGS_DIR')
    
    if custom_dir:
        # Expand ~ to home directory if used
        custom_dir = os.path.expanduser(custom_dir)
        return Path(custom_dir)
    else:
        # Use recordings folder in the same directory as the script
        script_dir = Path(__file__).parent
        return script_dir / "recordings"

# Configuration
SAMPLE_RATE = 44100
CHANNELS = 1
BASE_DIR = get_base_directory()

class SimpleAudioRecorder:
    def __init__(self):
        self.recording = None
        
    def list_microphones(self):
        """List available microphones"""
        print("\n🎤 Available Microphones:")
        print("-" * 40)
        
        devices = sd.query_devices()
        mic_list = []
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                mic_list.append((i, device['name']))
                print(f"{len(mic_list)}. {device['name']}")
        
        return mic_list
    
    def select_microphone(self):
        """Let user select microphone"""
        mic_list = self.list_microphones()
        
        if not mic_list:
            print("❌ No microphones found!")
            sys.exit(1)
        
        while True:
            try:
                choice = input(f"\nSelect microphone (1-{len(mic_list)}): ").strip()
                index = int(choice) - 1
                if 0 <= index < len(mic_list):
                    device_index, device_name = mic_list[index]
                    print(f"✅ Selected: {device_name}")
                    return device_index
                else:
                    print(f"❌ Please enter a number between 1 and {len(mic_list)}")
            except ValueError:
                print("❌ Please enter a valid number")
    
    def record_audio(self, device_index):
        """Record audio using sounddevice"""
        print("\n🔴 Recording... Press Enter to stop")
        
        # Start recording in a separate thread
        self.recording = []
        
        def callback(indata, frames, time, status):
            if status:
                print(f"Recording status: {status}")
            self.recording.append(indata.copy())
        
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                device=device_index,
                callback=callback
            ):
                input()  # Wait for user to press Enter
            
            print("⏹️  Recording stopped")
            
            # Concatenate all recorded chunks
            if self.recording:
                audio_data = np.concatenate(self.recording, axis=0)
                return audio_data
            else:
                print("❌ No audio recorded")
                return None
                
        except Exception as e:
            print(f"❌ Recording error: {e}")
            return None
    
    def save_audio(self, audio_data, filename):
        """Save recorded audio to file"""
        try:
            sf.write(filename, audio_data, SAMPLE_RATE)
            print(f"💾 Audio saved: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving audio: {e}")
            return False

class GeminiTranscriber:
    def __init__(self):
        self.setup_gemini()
    
    def setup_gemini(self):
        """Setup Gemini API"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY environment variable not set!")
            print("💡 Set it with: export GEMINI_API_KEY='your-api-key'")
            sys.exit(1)
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Gemini API configured")
    
    def transcribe_audio(self, audio_file):
        """Transcribe audio file using Gemini"""
        try:
            print("🤖 Transcribing audio with Gemini...")
            
            # Upload the audio file
            audio_file_obj = genai.upload_file(path=audio_file)
            
            # Create prompt for transcription
            prompt = """
            Please transcribe this audio file and format it as a clean, readable transcript.
            
            Guidelines:
            - Transcribe the speech accurately
            - Use proper punctuation and capitalisation
            - Spell in UK English
            - Break into paragraphs where natural pauses occur
            - Clean up any filler words (um, uh, etc.) unless they're meaningful
            - Add timestamps if there are significant topic changes
            - Make it coherent and well-formatted
            - I may say things then change my mind or correct myself, so please handle that gracefully
            - I may say things like "ignore this" or "forget what I just said",
            so please do not include those in the final transcript
            
            Please provide just the formatted transcript without any additional commentary.
            """
            
            # Generate transcription
            response = self.model.generate_content([prompt, audio_file_obj])
            
            if response.text:
                print("✅ Transcription completed")
                return response.text.strip()
            else:
                print("❌ No transcription received")
                return None
                
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return None

def create_folder_structure():
    """Create the base folder structure"""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Using directory: {BASE_DIR}")

def get_timestamp():
    """Get current timestamp in DDMMYYYY_HHMMSS format"""
    now = datetime.datetime.now()
    return now.strftime("%d%m%Y_%H%M%S")

def save_transcript(transcript, filename):
    """Save transcript to file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # Add header with timestamp
            header = f"Voice Dictation Transcript\n"
            header += f"Recorded: {datetime.datetime.now().strftime('%d %B %Y at %H:%M:%S')}\n"
            header += f"{'=' * 50}\n\n"
            
            f.write(header)
            f.write(transcript)
        
        print(f"📝 Transcript saved: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving transcript: {e}")
        return False

def main():
    print("🎙️  Voice Dictation Tool (Simple Version)")
    print("=" * 40)
    
    # Check dependencies
    try:
        import sounddevice as sd
        import soundfile as sf
        import google.generativeai as genai
        import numpy as np
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install with: pip install sounddevice soundfile google-generativeai numpy")
        sys.exit(1)
    
    # Create folder structure
    create_folder_structure()
    
    # Get timestamp for this session
    timestamp = get_timestamp()
    session_dir = BASE_DIR / timestamp
    session_dir.mkdir(exist_ok=True)
    
    # File paths
    audio_file = session_dir / f"{timestamp}.wav"
    transcript_file = session_dir / f"{timestamp}.txt"
    
    print(f"📁 Session folder: {session_dir}")
    
    # Initialize components
    recorder = SimpleAudioRecorder()
    transcriber = GeminiTranscriber()
    
    try:
        # Select microphone
        device_index = recorder.select_microphone()
        
        # Record audio
        audio_data = recorder.record_audio(device_index)
        
        if audio_data is not None:
            # Save audio
            if recorder.save_audio(audio_data, str(audio_file)):
                # Transcribe audio
                transcript = transcriber.transcribe_audio(str(audio_file))
                
                if transcript:
                    # Save transcript
                    if save_transcript(transcript, str(transcript_file)):
                        print(f"\n🎉 Session completed successfully!")
                        print(f"📁 Files saved in: {session_dir}")
                        print(f"🎵 Audio: {audio_file.name}")
                        print(f"📝 Transcript: {transcript_file.name}")
                    else:
                        print("❌ Failed to save transcript")
                else:
                    print("❌ Failed to transcribe audio")
            else:
                print("❌ Failed to save audio")
        else:
            print("❌ Failed to record audio")
    
    except KeyboardInterrupt:
        print("\n⚠️  Recording cancelled by user")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
