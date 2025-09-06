# 🎙️ Voice Dictation Tool with AI Search

A powerful voice dictation tool that records audio, transcribes it using Google's Gemini AI, and provides semantic search across all your transcripts with beautiful terminal interfaces.

## ✨ Features

- 🎤 **Simple audio recording** with press-Enter-to-stop interface
- 🤖 **AI transcription** using Google Gemini API
- 🔍 **Semantic search** across all transcripts with vector embeddings
- 🗣️ **Voice search** - search your transcripts using spoken queries
- 📁 **Smart organization** with timestamped session folders
- 📋 **Intelligent listing** that scales with large collections
- 🎨 **Beautiful terminal interface** with rich formatting
- ⚙️ **Simple configuration** with user-friendly setup
- 🏷️ **Smart folder management** with vectorization status tracking
- 🔒 **Privacy controls** for sensitive recordings
- 🗑️ **Granular removal** of specific transcripts from search index

## 🚀 Quick Setup

1. **Clone and enter directory**:
   ```bash
   git clone https://github.com/benjamayden/dictate.git
   cd dictate
   ```

2. **Add your API key**:
   - Open `config.txt` in any text editor
   - Replace `your-api-key-here` with your actual Gemini API key
   - Get your API key from: [Google AI Studio](https://aistudio.google.com/app/apikey)

3. **Customize settings** (optional):
   ```bash
   # Edit config.txt to customize:
   DICTATE_RECORDINGS_DIR=/your/preferred/path    # Custom directory
   DICTATE_ALIAS_NAME=rec                         # Custom alias (default: dictate)
   TRANSCRIPT_FORMAT=md                           # 'txt' or 'md' format
   AUTO_OPEN_TRANSCRIPT=true                      # Auto-open after transcription
   ```

4. **Run setup**:
   ```bash
   ./setup.sh
   ```

That's it! The setup script will:
- ✅ Create a virtual environment
- ✅ Install all dependencies  
- ✅ Create your `.env` file
- ✅ Set up shell aliases (customizable)
- ✅ Clear your API key from `config.txt` for security

## 🎯 Usage

After setup, restart your terminal and use your custom aliases:

```bash
dictate              # Start recording (or your custom alias like 'rec')
vnotes               # Open recordings folder (or your custom alias)
```

## 📋 Available Commands

### Core Recording & Transcription
```bash
dictate record                      # Start recording and transcribe
dictate record --output "meeting"   # Record with custom filename
dictate record --no-vectorize       # Record without adding to search index (private)
dictate transcribe audio.wav       # Transcribe existing audio file
```

### Smart Listing (Never Overwhelming!)
```bash
dictate list                     # Show last 7 days (default)
dictate list --days 14          # Show last 14 days
dictate list --date 2025-09-04   # Show recordings around specific date (±2 days)  
dictate list --month 2025-09     # Show entire month
```

### Search & Discovery
```bash
dictate search "project planning" # Text search (auto-saves results)
dictate find                     # Voice search (record your query)
dictate find "meeting notes"     # Voice search with fallback text
dictate show 04092025_155531     # Display specific transcript
```

### Vector Search Management
```bash
dictate vectorize               # Index all transcripts for search
dictate inspect                 # View vector store status and stats
dictate inspect --details       # Show sample documents and detailed stats
dictate remove session_name     # Remove specific transcript from search index
dictate reset-vectors           # Completely wipe vector store (with confirmation)
```

### System & Configuration
```bash
dictate list-mics              # Show available microphones
dictate config                 # Show current configuration
dictate --help                 # Show all commands
```

## 📁 File Organization & Status System

The tool organizes everything in clean session folders with intelligent status tracking:

```
recordings/
├── 04092025_155531/           # Timestamped session folder (not yet vectorized)
│   ├── meeting_notes.wav      # Audio recording
│   └── meeting_notes.md       # Transcript (or .txt)
├── 04092025_160245_v/         # Vectorized session (in search index)
│   ├── brainstorm.wav
│   └── brainstorm.txt
├── 04092025_161500_nv/        # Private session (never vectorized)
│   ├── personal_notes.wav
│   └── personal_notes.txt
├── searches/                  # Auto-saved search results
│   ├── project_planning_20250904.txt
│   └── voice_search_20250904.txt
└── vector_store/              # Search index (ChromaDB)
    └── chroma.sqlite3
```

### Folder Status System:
- **No suffix**: Newly recorded, not yet vectorized
- **`_v` suffix**: Successfully vectorized and in search index  
- **`_nv` suffix**: Marked as no-vectorize (private/sensitive recordings)

### Smart Workflow:
1. **Record**: `dictate record` creates clean timestamped folders
2. **Vectorize**: `dictate vectorize` processes new folders and adds `_v` suffix
3. **Privacy**: `dictate record --no-vectorize` creates `_nv` folders that are never indexed
4. **Management**: `dictate remove session_name` removes from index and reverts `_v` suffix
5. **Status**: `dictate list` shows visual indicators for each folder's status

## 🎨 Beautiful Terminal Experience

The tool features clean, functional terminal output:

- 🎤 Simple recording start/stop indicators
- 📊 Progress bars for transcription and vectorization
- 🎯 Formatted search results with similarity scores
- 📄 Transcript previews in clean panels
- 📅 Date-organized listings with status indicators
- ✅ Clear success/error messages with helpful guidance
- 🏷️ **Status indicators** showing vectorization state of each session
- 📊 **Vector store inspection** with sample documents and statistics

## 🔒 Privacy & Control Features

### Private Recordings
```bash
dictate record --no-vectorize    # Creates _nv folders that are never indexed
rec -nv                         # Short alias for private recordings  
```

### Granular Management
```bash
dictate remove session_name     # Remove specific transcript from search
dictate inspect                 # Check what's currently indexed
dictate reset-vectors          # Nuclear option - wipe everything
```

### Smart Status Tracking
The tool automatically tracks the vectorization status of each recording:
- 📁 **Clean folders**: Not yet processed
- 🔍 **Vectorized folders** (`_v`): In search index  
- 🔒 **Private folders** (`_nv`): Never indexed
- 📋 **Visual indicators**: Clear status in `dictate list`

## 🔍 Search Features

### Text Search
```bash
dictate search "meeting with client"
# Returns semantically similar content, even if exact words don't match
# Automatically saves results to searches/ folder
```

### Voice Search  
```bash
dictate find
# Records your voice query, transcribes it, then searches
# Perfect for hands-free operation
```

### Vector Store Management
```bash
dictate inspect                 # Check vector store status
dictate inspect --details       # View sample documents and detailed stats
dictate remove session_name     # Remove specific transcript from index
dictate reset-vectors          # Complete wipe (with confirmation)
```

### Smart Results
- **Similarity scores** show relevance
- **Automatic chunking** finds specific sections
- **Context preservation** maintains meaning
- **Export ready** results saved as txt files
- **Duplicate prevention** with smart folder status tracking

## 🛠️ Troubleshooting

### Setup Issues
- **Permission denied**: `chmod +x setup.sh`
- **Python not found**: Install Python 3.7+ from python.org
- **pip not found**: `python3 -m ensurepip --upgrade`

### Audio Issues  
- **No microphone detected**: `dictate list-mics` to see available devices
- **Permission denied (macOS)**: System Preferences → Privacy → Microphone → Terminal
- **Poor audio quality**: Adjust `AUDIO_QUALITY=high` in config.txt

### API Issues
- **Invalid API key**: Get new key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Quota exceeded**: Check your API usage limits
- **Network errors**: Verify internet connection

### Search Issues
- **No results found**: Run `dictate vectorize` to index transcripts first
- **Poor search results**: Try different keywords or use voice search
- **Duplicate results**: The system now prevents duplicate indexing with `_v` suffixes
- **Missing transcripts**: Check `dictate inspect` to see what's actually indexed
- **Vector store corruption**: Use `dictate reset-vectors` to start fresh

## 📚 Examples

### Daily Workflow
```bash
# Morning standup
rec --output "standup_notes"

# Private personal notes (won't be searchable)
rec --no-vectorize --output "personal_thoughts"

# Later, find that meeting
dictate show standup

# Index new recordings for search
dictate vectorize

# Search across all meetings
dictate search "action items discussed yesterday"

# Voice search for something specific
dictate find  # Then speak: "what did John say about the budget?"

# Check what's been indexed
dictate inspect
```

### Privacy & Management
```bash
# Record private session (never indexed)
dictate record --no-vectorize

# Remove specific transcript from search
dictate remove old_meeting

# Check vector store status
dictate inspect --details

# Complete vector store reset
dictate reset-vectors
```

### Batch Operations
```bash
# Index all existing transcripts
dictate vectorize

# See what's been recorded recently (with status indicators)
dictate list

# Look at a specific month
dictate list --month 2025-09

# Show configuration
dictate config
```

## 🔄 Updating

To update your installation:

```bash
cd dictate
git pull
./setup.sh  # Re-run setup to get new features
```

Your configuration and recordings are preserved.

## 🤝 Requirements

- **Python 3.7+** 
- **Internet connection** (for AI transcription)
- **Microphone access**
- **Google Gemini API key** (free tier available)

---

**Happy dictating!** 🎙️✨
