## Changelog

### [Unreleased]
- Microphone auto-selection with preference persistence
  - Adds `MicrophoneManager` that remembers last-used mic and scores devices to auto-select the best available (external/pro brands prioritized).
  - Removes manual microphone prompt; recording starts immediately using the selected device.

- LLM-based session folder naming
  - After transcription, generates a concise session name via Gemini and renames the session folder to `{name}_{timestamp}`.
  - Names are sanitized to safe slugs (lowercase, underscores).

- Transcript file opening prompt
  - After completion, asks user if they want to open the transcript file in the default text editor.
  - Simple y/n prompt that works from terminal or any environment.
  - Cross-platform support (macOS: `open`, Linux: `xdg-open`, Windows: `start`).

- Notes folder access alias
  - New `NOTES_FOLDER_ALIAS` environment variable to customize the command for opening the notes folder.
  - Default command: `goNotes` (configurable in .env file).
  - Automatically detects the correct notes directory path from `DICTATE_RECORDINGS_DIR` or falls back to default.

### Usage Notes
- Normal recording: `python3 dictate.py`
- Transcribe existing file: `python3 dictate.py transcribe /path/to/audio.wav`
- Session folders will now be named like `idea_brainstorm_22082025_073740`.

### Environment
- Requires `GEMINI_API_KEY` in `.env`.


