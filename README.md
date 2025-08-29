# 🎙️ Voice Dictation Tool

Record audio and transcribe it using Google's Gemini AI.

## Quick Setup

1. **Get API Key**: [Google AI Studio](https://aistudio.google.com/app/apikey)
2. **Run setup**:
   ```bash
   ./setup.sh
   ```
3. **Add your API key**:
   ```bash
   nano .env
   # Replace 'your-api-key-here' with your actual key
   ```
4. **Create alias** (optional):
   ```bash
   ./create_alias.sh
   ```
   This creates both the `dictate` command and `goNotes` command for easy access.

## Usage

```bash
dictate              # If you set up the alias
python3 dictate.py   # Direct execution
```

## Configuration

Edit `.env` to customize:

```bash
# Required
GEMINI_API_KEY=your-actual-api-key

# Optional - where to save recordings (default: ./recordings/)
DICTATE_RECORDINGS_DIR=~/Desktop/voice-notes

# Optional - custom command name (default: dictate)
DICTATE_ALIAS_NAME=listen

# Optional - custom notes folder command (default: goNotes)
NOTES_FOLDER_ALIAS=notes
```

## How It Works

1. Choose microphone
2. Press Enter → speak → Press Enter
3. Audio saved + AI transcription created
4. Files saved in timestamped folders

## Files Created

```
recordings/
└── DDMMYYYY_HHMMSS/
    ├── DDMMYYYY_HHMMSS.wav  # Audio
    └── DDMMYYYY_HHMMSS.txt  # Transcript
```

## Troubleshooting

- **Not f
- **Permission denied**: `chmod +x setup.sh`
- **Microphone access**: Check System Preferences → Privacy → Microphone
- **Dependencies**: `pip3 install sounddevice soundfile google-generativeai numpy python-dotenv`

## Requirements

- Python 3.7+
- Internet connection (for AI transcription)
- Microphone
