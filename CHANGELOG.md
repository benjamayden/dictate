## Changelog

### [Unreleased]
- Microphone auto-selection with preference persistence
  - Adds `MicrophoneManager` that remembers last-used mic and scores devices to auto-select the best available (external/pro brands prioritized).
  - Removes manual microphone prompt; recording starts immediately using the selected device.

- LLM-based session folder naming
  - After transcription, generates a concise session name via Gemini and renames the session folder to `{name}_{timestamp}`.
  - Names are sanitized to safe slugs (lowercase, underscores).

### Usage Notes
- Normal recording: `python3 dictate.py`
- Transcribe existing file: `python3 dictate.py transcribe /path/to/audio.wav`
- Session folders will now be named like `idea_brainstorm_22082025_073740`.

### Environment
- Requires `GEMINI_API_KEY` in `.env`.


