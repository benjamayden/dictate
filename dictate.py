#!/usr/bin/env python3
"""
Voice Dictation Tool

A simple script to record audio, transcribe it using Gemini, and save both
the audio file and formatted transcript.

Usage:
    python3 dictate.py                    # Record and transcribe
    python3 dictate.py transcribe <file>  # Transcribe existing file
    
Requirements:
    pip install sounddevice soundfile google-genai numpy python-dotenv

Setup:
    1. Copy CONFIGURATION_TEMPLATE.txt to .env
    2. Update .env with your API key and preferred settings
"""

import os
import sys
import time
import datetime
import argparse
import shutil
import json
import re
import numpy as np
import sounddevice as sd
import soundfile as sf
from google import genai
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class MicrophoneManager:
    """Microphone auto-selection and preference persistence.

    Notes:
    - Prefers last-used mic when available
    - Otherwise scores external/pro brands higher and selects highest score
    - Preferences stored at ~/.dictate_preferences.json
    """

    def __init__(self):
        self.preferences_path = Path.home() / ".dictate_preferences.json"
        self.preferences = self._load_preferences()

    def _load_preferences(self):
        try:
            if self.preferences_path.exists():
                with open(self.preferences_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load preferences: {e}")
        return {"last_microphone": None}

    def _save_preferences(self):
        try:
            with open(self.preferences_path, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save preferences: {e}")

    def _score_microphone(self, device_index, device_name):
        score = 0
        name = device_name.lower()
        try:
            info = sd.query_devices(device_index)
            sample_rate = info.get('default_samplerate', 0) or 0
            channels = info.get('max_input_channels', 0) or 0
        except Exception:
            sample_rate = 0
            channels = 0

        # Prefer last used
        if device_index == self.preferences.get('last_microphone'):
            score += 40

        # External hints
        if any(x in name for x in ['usb', 'bluetooth', 'external', 'interface']):
            score += 100

        # Pro brands
        if any(x in name for x in ['samson', 'shure', 'rode', 'audio-technica', 'blue', 'yeti', 'sennheiser', 'neumann']):
            score += 50

        # Built-in penalty
        if any(x in name for x in ['built-in', 'builtin', 'internal', 'default']):
            score -= 50

        # Technical capabilities
        if sample_rate >= 48000:
            score += 20
        elif sample_rate >= 44100:
            score += 10
        if channels >= 2:
            score += 5

        return score

    def auto_select_best_microphone(self):
        devices = sd.query_devices()
        candidates = []
        for i, device in enumerate(devices):
            if device.get('max_input_channels', 0) > 0:
                name = device.get('name', str(i))
                candidates.append((i, name))

        if not candidates:
            print("❌ No microphones found!")
            sys.exit(1)

        # If last mic still available, prefer it and print info
        last_idx = self.preferences.get('last_microphone')
        if last_idx is not None and any(ci == last_idx for ci, _ in candidates):
            name = next(n for ci, n in candidates if ci == last_idx)
            print(f"🎤 Microphone: using last used → {name}")
            return last_idx

        # Score and choose best
        scored = []
        for idx, name in candidates:
            scored.append((idx, name, self._score_microphone(idx, name)))
        scored.sort(key=lambda x: x[2], reverse=True)

        best_idx, best_name, best_score = scored[0]
        print("🎤 Microphone auto-selected:")
        print(f"   Selected: {best_name} (Score: {best_score})")
        if len(scored) > 1:
            runner = scored[1]
            print(f"   Runner-up: {runner[1]} (Score: {runner[2]})")

        # Persist selection for next run
        self.preferences['last_microphone'] = best_idx
        self._save_preferences()

        return best_idx

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

class FileProcessor:
    """Handles file operations and organization"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
    
    def create_session_folder(self, timestamp: str) -> Path:
        """Create a new session folder"""
        session_dir = self.base_dir / timestamp
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def organize_existing_file(self, file_path: Path) -> tuple[Path, Path]:
        """Move existing file to recordings directory and create transcript path"""
        timestamp = get_timestamp()
        session_dir = self.create_session_folder(timestamp)
        
        # Move file to session directory
        new_audio_path = session_dir / f"{timestamp}.wav"
        shutil.copy2(file_path, new_audio_path)
        
        # Create transcript path
        transcript_path = session_dir / f"{timestamp}.txt"
        
        print(f"📁 File organized in session: {session_dir}")
        print(f"🎵 Audio: {new_audio_path.name}")
        print(f"📝 Transcript: {transcript_path.name}")
        
        return new_audio_path, transcript_path

class TranscriptionService:
    """Handles audio transcription using Gemini API"""
    
    def __init__(self):
        self.setup_gemini()
    
    def setup_gemini(self):
        """Setup Gemini API"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY environment variable not set!")
            print("💡 Set it with: export GEMINI_API_KEY='your-api-key'")
            sys.exit(1)
        
        # Set the environment variable for the client
        os.environ['GOOGLE_API_KEY'] = api_key
        self.client = genai.Client()
        print("✅ Gemini API configured")
    
    def transcribe_audio(self, audio_file: Path) -> str:
        """Transcribe audio file using Gemini"""
        try:
            print("🤖 Transcribing audio with Gemini...")
            print(f"🎵 Audio file: {audio_file}")
            
            # Upload the audio file using the correct method
            try:
                print("🔄 Uploading audio file...")
                uploaded_audio = self.client.files.upload(file=str(audio_file))
                print("✅ Audio uploaded successfully")
                
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
                
                # Prepare multimodal content with uploaded file
                contents = [
                    prompt,
                    uploaded_audio,
                ]
                
                print("🔄 Generating transcription...")
                
                # Generate transcription using the uploaded file
                response = self.client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=contents
                )
                
                if response and hasattr(response, 'text') and response.text:
                    print("✅ Transcription completed")
                    return response.text.strip()
                else:
                    print("❌ No transcription received - response was empty")
                    return None
                    
            except Exception as e:
                print(f"❌ Upload failed: {e}")
                print("⚠️ Falling back to text-only mode (no actual audio transcription)")
                
                # Fallback: just return a message indicating the issue
                fallback_message = f"""
                ⚠️ Audio transcription failed - file upload error.
                
                Audio file location: {audio_file}
                Error: {str(e)}
                
                Please check your audio file and API configuration.
                """
                
                return fallback_message.strip()
                
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            print(f"🔍 Error type: {type(e).__name__}")
            import traceback
            print(f"🔍 Full traceback:")
            traceback.print_exc()
            return None

    def generate_session_name(self, transcript: str) -> str:
        """Use LLM to generate a concise session name from transcript.

        Returns a short descriptive name (lowercase, underscores later applied).
        """
        try:
            prompt = (
                "Read the transcript and propose a concise 3-5 word session name "
                "that captures the main topic. Rules: lowercase words, no punctuation, "
                "no dates/times, no emojis, use spaces between words only. Return name only."
            )
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[prompt, transcript]
            )
            if response and hasattr(response, 'text') and response.text:
                name = response.text.strip().lower()
            else:
                name = "session"
        except Exception:
            name = "session"
        return name

def _sanitize_session_name(name: str) -> str:
    """Sanitize a name into a safe folder slug using underscores.

    - Lowercase
    - Replace non alphanumeric with single underscore
    - Trim underscores
    - Collapse multiple underscores
    """
    if not name:
        return "session"
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "session"

class SimpleAudioRecorder:
    """Handles audio recording functionality"""
    
    def __init__(self):
        self.recording = None
        self.mic_manager = MicrophoneManager()
        
    def select_microphone(self):
        """Auto-select best available microphone without prompting"""
        return self.mic_manager.auto_select_best_microphone()
    
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

def create_folder_structure():
    """Create the base folder structure"""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"💾 Using directory: {BASE_DIR}")

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

def transcribe_file(file_path: str):
    """Transcribe an existing audio file"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    if not file_path.suffix.lower() in ['.wav', '.mp3', '.m4a', '.flac']:
        print(f"❌ Unsupported audio format: {file_path.suffix}")
        return False
    
    # Initialize services
    file_processor = FileProcessor(BASE_DIR)
    transcriber = TranscriptionService()
    
    try:
        # Organize file into recordings directory
        audio_path, transcript_path = file_processor.organize_existing_file(file_path)
        
        # Transcribe audio
        transcript = transcriber.transcribe_audio(audio_path)
        
        if transcript:
            # Generate LLM-based session name and rename folder
            try:
                raw_name = transcriber.generate_session_name(transcript)
                slug = _sanitize_session_name(raw_name)
                current_dir = audio_path.parent
                timestamp = current_dir.name
                new_dir = current_dir.parent / f"{slug}_{timestamp}"
                if new_dir != current_dir:
                    current_dir.rename(new_dir)
                    audio_path = new_dir / audio_path.name
                    transcript_path = new_dir / transcript_path.name
                print(f"🏷️  Session named: {slug}")
            except Exception as e:
                print(f"⚠️  Could not rename session folder: {e}")
            # Save transcript
            if save_transcript(transcript, transcript_path):
                print(f"\n🎉 Transcription completed successfully!")
                print(f"📁 Files organized in: {transcript_path.parent}")
                return True
            else:
                print("❌ Failed to save transcript")
                return False
        else:
            print("❌ Failed to transcribe audio")
            return False
    
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return False

def record_and_transcribe():
    """Record audio and transcribe it"""
    print("🎙️  Voice Dictation Tool - Recording Mode")
    print("=" * 40)
    
    # Check dependencies
    try:
        import sounddevice as sd
        import soundfile as sf
        from google import genai
        import numpy as np
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install with: pip install sounddevice soundfile google-genai numpy")
        sys.exit(1)
    
    # Create folder structure
    create_folder_structure()
    
    # Get timestamp for this session
    timestamp = get_timestamp()
    file_processor = FileProcessor(BASE_DIR)
    session_dir = file_processor.create_session_folder(timestamp)
    
    # File paths
    audio_file = session_dir / f"{timestamp}.wav"
    transcript_file = session_dir / f"{timestamp}.txt"
    
    print(f"📁 Session folder: {session_dir}")
    
    # Initialize components
    recorder = SimpleAudioRecorder()
    transcriber = TranscriptionService()
    
    try:
        # Select microphone
        device_index = recorder.select_microphone()
        
        # Record audio
        audio_data = recorder.record_audio(device_index)
        
        if audio_data is not None:
            # Save audio
            if recorder.save_audio(audio_data, str(audio_file)):
                # Transcribe audio
                transcript = transcriber.transcribe_audio(audio_file)
                
                if transcript:
                    # Generate LLM-based session name and rename folder
                    try:
                        raw_name = transcriber.generate_session_name(transcript)
                        slug = _sanitize_session_name(raw_name)
                        current_dir = audio_file.parent
                        timestamp = current_dir.name
                        new_dir = current_dir.parent / f"{slug}_{timestamp}"
                        if new_dir != current_dir:
                            current_dir.rename(new_dir)
                            audio_file = new_dir / audio_file.name
                            transcript_file = new_dir / transcript_file.name
                            # ensure subsequent messages reflect renamed folder
                            session_dir = new_dir
                        print(f"🏷️  Session named: {slug}")
                    except Exception as e:
                        print(f"⚠️  Could not rename session folder: {e}")
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

def main():
    parser = argparse.ArgumentParser(description="Voice Dictation Tool")
    parser.add_argument('action', nargs='?', default='record', 
                       choices=['record', 'transcribe'],
                       help='Action to perform (default: record)')
    parser.add_argument('file', nargs='?', help='Audio file to transcribe')
    
    args = parser.parse_args()
    
    if args.action == 'transcribe':
        if not args.file:
            print("❌ Please provide a file path for transcription")
            print("Usage: python3 dictate.py transcribe /path/to/audio.wav")
            sys.exit(1)
        transcribe_file(args.file)
    else:
        record_and_transcribe()

if __name__ == "__main__":
    main()