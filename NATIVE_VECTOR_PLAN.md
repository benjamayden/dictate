# Voice Dictation Tool - Native Vector Store Implementation Plan

## 🎯 Vision: Pure Native Python with ChromaDB Vector Store

A powerful voice dictation tool that runs entirely natively with full vector search capabilities - **no Docker required**.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Native Audio  │───▶│  Gemini API      │───▶│  ChromaDB       │
│   Recording     │    │  Transcription   │    │  Vector Store   │
│   (PyAudio)     │    │  + Embeddings    │    │  (File-based)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Key Benefits:**
- ✅ Full microphone access (native Python)
- ✅ Persistent vector search (ChromaDB)
- ✅ Zero Docker complexity
- ✅ Unified Gemini ecosystem
- ✅ Fast startup and operation
- ✅ Cross-platform compatibility

## 📋 Implementation Phases

### Phase 1: Core Native Implementation ⚡

**Branch:** `feature/native-core`

#### 1.1: Project Structure Redesign
```
dictate/
├── dictate.py                 # Main application
├── vector_store.py            # ChromaDB vector operations
├── audio_recorder.py          # Native audio recording
├── transcription.py           # Gemini API integration
├── requirements.txt           # Native Python dependencies
├── setup.py                   # Simple pip-installable package
├── .env.template             # Configuration template
└── recordings/               # Local storage
    ├── audio/               # WAV files
    ├── transcripts/         # Text files
    └── vector_store/        # ChromaDB persistence
```

#### 1.2: Dependencies
```python
# requirements.txt - Clean and focused
sounddevice==0.4.6
soundfile==0.12.1
google-genai>=0.1.0
chromadb>=0.4.0
python-dotenv==1.0.0
click>=8.0.0          # For CLI interface
rich>=13.0.0          # For beautiful terminal output
numpy>=1.24.3
```

#### 1.3: Core Modules

**`audio_recorder.py`** - Native audio recording
```python
class AudioRecorder:
    """High-quality native audio recording with real-time feedback"""
    
    def __init__(self, sample_rate=44100, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.frames = []
        self.is_recording = False
        self.auto_save_interval = 10  # Save every 10 seconds
        self.current_file = None
    
    def start_recording(self):
        """Start recording with visual feedback and auto-save protection"""
        
    def _auto_save_worker(self):
        """Background thread that saves audio every 10 seconds"""
        # Continuously overwrites temp file to protect against crashes
        
    def stop_recording(self, filename):
        """Stop and save final recording"""
        
    def list_microphones(self):
        """Show available audio devices"""
        
    def _emergency_cleanup(self):
        """Handle unexpected termination - keeps last auto-save"""
```

**`vector_store.py`** - ChromaDB integration
```python
class VectorStoreManager:
    """Persistent vector store using ChromaDB"""
    
    def __init__(self, persist_directory="./recordings/vector_store"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection("transcripts")
        
    def add_transcript(self, transcript_path: Path):
        """Chunk and vectorize transcript"""
        
    def search_similar(self, query: str, limit: int = 5):
        """Semantic search across all transcripts"""
        
    def voice_search(self, audio_query_path: Path):
        """Transcribe audio query and search"""
```

**`transcription.py`** - Gemini API wrapper
```python
class GeminiTranscriber:
    """Unified Gemini API for transcription and embeddings"""
    
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        
    def transcribe_audio(self, audio_path: Path) -> str:
        """Convert audio to text using Gemini"""
        
    def get_embedding(self, text: str) -> list:
        """Get text embedding using Gemini"""
        
    def enhance_transcript(self, text: str) -> str:
        """Add timestamps, formatting, structure"""
```


### Phase 2: CLI and User Experience 🎨

**Branch:** `feature/native-cli`

#### 2.1: Beautiful CLI Interface
```python
# Using Click + Rich for gorgeous terminal experience
@click.group()
def cli():
    """🎙️ Voice Dictation Tool with AI Search"""

@cli.command()
@click.option('--duration', default=None, help='Max recording duration')
@click.option('--output', default=None, help='Custom output filename')
def record(duration, output):
    """🎤 Record and transcribe audio"""

@cli.command()
@click.argument('query')
def search(query):
    """🔍 Search transcripts (text or audio file)"""

@cli.command()
def find():
    """🗣️ Voice search your transcripts"""

@cli.command()
def embed():
    """🧠 Embed transcripts for semantic search (replaces vectorize)"""

@cli.command()
def shortcuts():
    """⚡ Show all available command shortcuts"""
```

#### 2.2: Rich Terminal Output
```python
# Beautiful progress bars, status displays, and formatting
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.panel import Panel

console = Console()

# Example outputs:
console.print("🎤 Recording...", style="bold green")
console.print(Panel("Transcript content here", title="📄 Transcription"))

# Progress bars for vectorization
with Progress() as progress:
    task = progress.add_task("Vectorizing transcripts...", total=100)
```


#### 2.3: Configuration Management
```python
# .env.template
GEMINI_API_KEY=your-api-key-here
RECORDINGS_DIR=~/dictate/recordings
PREFERRED_MICROPHONE=default
CHUNK_SIZE=500
CHUNK_OVERLAP=50
AUTO_EMBED=true
AUDIO_QUALITY=high
# Shortcuts configuration
SHORTCUT_RECORD=rec
SHORTCUT_SEARCH=s
SHORTCUT_FIND=f
SHORTCUT_EMBED=e
```

### Phase 3: Advanced Features 🚀

**Branch:** `feature/native-advanced`

#### 3.1: Intelligent Session Management
```python
class SessionManager:
    """Automatic organization and naming of recordings"""
    
    def create_session(self, transcript_preview: str):
        """Generate descriptive folder names from content"""
        # "20250904_143022_project_planning_session/"
        
    def auto_categorize(self, transcript: str):
        """Use Gemini to categorize and tag transcripts"""
        
    def suggest_related(self, current_transcript: str):
        """Find related previous recordings"""
```

#### 3.2: Document Enhancement
```python
class DocumentEnhancer:
    """Enhance documents with related transcript information"""
    
    def enhance_document(self, document_path: Path):
        """Add related information section to any document"""
        
    def create_summary(self, transcript_paths: list):
        """Generate meeting summaries from multiple transcripts"""
        
    def extract_action_items(self, transcript: str):
        """Pull out tasks and action items"""
```

#### 3.3: Export and Integration
```python
class ExportManager:
    """Export transcripts in various formats"""
    
    def export_markdown(self, session_id: str):
        """Export as structured Markdown"""
        
    def export_notion(self, session_id: str):
        """Direct Notion integration"""
        
    def export_obsidian(self, session_id: str):
        """Obsidian vault integration"""
```

### Phase 4: Installation and Distribution 📦

**Branch:** `feature/native-packaging`

#### 4.1: Simple Installation
```bash
# Git clone installation (clean and simple)
git clone https://github.com/benjamayden/dictate.git
cd dictate
pip install -e .  # Installs dependencies + creates CLI

# Optional: One-line installer script
curl -sSL https://raw.githubusercontent.com/benjamayden/dictate/main/install.sh | bash
```

#### 4.2: Cross-Platform Setup
```python
# setup.py - simple and focused
setup(
    name="dictate",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'dictate=dictate.cli:main',
        ],
    },
    install_requires=[
        'sounddevice>=0.4.6',
        'google-genai>=0.1.0',
        'chromadb>=0.4.0',
        'click>=8.0.0',
        'rich>=13.0.0',
        # Platform-specific audio backends handled automatically
    ],
)
```

#### 4.3: Shell Integration
```bash
# Automatic shell alias setup with user customization
dictate setup-aliases

# Respects user's .env settings for alias names:
# If ALIAS_RECORD=rec, creates: alias rec="dictate record"
# If ALIAS_SEARCH=s, creates: alias s="dictate search"

# Adds to ~/.zshrc or ~/.bashrc based on user's environment variables:
alias ${ALIAS_RECORD:-record}="dictate record"     # Default: record
alias ${ALIAS_SEARCH:-search}="dictate search"     # Default: search  
alias ${ALIAS_FIND:-find-voice}="dictate find"     # Default: find-voice
alias ${ALIAS_LIST:-list}="dictate list"           # Default: list

# Example with custom short aliases:
# ALIAS_RECORD=r
# ALIAS_SEARCH=s  
# ALIAS_FIND=f
# ALIAS_LIST=l
# Results in: r, s, f, l commands
```

## � Smart Listing System

### Scalable Date-Based Listing
```python
class RecordingLister:
    """Smart listing that scales with large recording collections"""
    
    def list_recent(self, days=7):
        """Show last week by default - won't overwhelm user"""
        # 📅 September 1-7, 2025 (7 recordings)
        #    🎤 project_planning_discussion (3:45)
        #    🎤 client_meeting_notes (12:30)
        
    def list_around_date(self, target_date, window=2):
        """Show recordings around specific date (±2 days)"""
        # dictate list 2025-09-04
        # Shows: Sept 2, 3, 4, 5, 6 recordings
        
    def list_month(self, year, month):
        """For power users who want to see more"""
        # dictate list --month 2025-09
        # Groups by weeks within month
```

### Example Outputs
```bash
$ dictate list
📅 Last 7 days (12 recordings)

September 7, 2025
   🎤 weekend_brainstorm (2:15)

September 4, 2025  
   🎤 project_planning (3:45)
   🎤 client_meeting (12:30)

September 3, 2025
   🎤 technical_discussion (8:22)
   
# Clean, scannable, never overwhelming

$ dictate list 2025-09-04
📅 Around September 4, 2025 (±2 days)

September 2-6, 2025 (8 recordings)
   [Same format as above]
```

## �🚨 Terminal Interruption Handling

### Smart Auto-Save Strategy
```python
# Continuous protection without performance impact
class AudioRecorder:
    def __init__(self):
        self.auto_save_interval = 10  # seconds
        self.temp_file = "recording_temp.wav"
        
    def start_recording(self):
        # Start background auto-save thread
        threading.Timer(self.auto_save_interval, self._auto_save).start()
        
    def _auto_save(self):
        """Save current audio buffer every 10 seconds"""
        # Overwrites temp file each time
        # Low performance impact - just writes existing buffer
        if self.is_recording:
            self._save_current_buffer_to_temp()
            # Schedule next auto-save
            threading.Timer(self.auto_save_interval, self._auto_save).start()
    
    def _handle_crash(self):
        """If terminal closes unexpectedly"""
        # temp_file contains recording up to last 10-second mark
        # User only loses max 10 seconds
        if os.path.exists(self.temp_file):
            final_name = f"recovered_{timestamp()}.wav"
            os.rename(self.temp_file, final_name)
            print(f"🚨 Recovered recording: {final_name}")
```

### Recovery Workflow
```bash
# If terminal crashes during recording:
# 1. Tool auto-saved every 10 seconds to temp file
# 2. On next startup, tool checks for temp files
# 3. Prompts user: "Found interrupted recording, recover?"
# 4. Moves temp file to proper filename
# 5. User loses max 10 seconds of audio

dictate recover  # Manual recovery command
# "Found recording_temp.wav (3:45 duration)"
# "Recover as: 20250904_interrupted_meeting.wav? (y/n)"
```

## 🎯 Core Commands Design


### Primary Commands
```bash
# Recording and transcription
dictate record                    # Start recording session
dictate record --duration 300     # Record for 5 minutes max
dictate transcribe audio.wav      # Transcribe existing file

# Search and discovery
# All search results are automatically exported to the searches/ folder
dictate search "project planning"  # Text search
dictate find                      # Voice search (record query)
dictate find audio_query.wav      # Search with audio file

# Management (Smart Scaling)
dictate list                      # Show last week's recordings only
dictate list 2025-09-04           # Show recordings around specific date (±2 days)
dictate show session_id           # Display specific transcript
dictate export session_id         # Export in various formats
dictate shortcuts                 # Show all available command shortcuts
```


### Advanced Commands
```bash
# Embedding operations
dictate embed                     # Add all transcripts to semantic search
dictate embed --rebuild           # Rebuild entire vector store
dictate embed document.txt        # Add specific text file to search

# Document enhancement
dictate enhance document.txt            # Add related info to document
dictate summarize session1 session2     # Create summary from multiple
dictate actions document.txt            # Extract action items from session

# Configuration
dictate config                    # Show current configuration
dictate config set api_key YOUR_KEY   # Set configuration values
dictate setup                     # Interactive setup wizard
```

## 🔧 Configuration System


### Environment Variables
```bash
# Core settings
GEMINI_API_KEY=your-api-key
DICTATE_HOME=~/dictate           # Base directory
PREFERRED_MIC=default            # Audio device (robust fallback if unavailable)

# Embedding settings
CHUNK_SIZE=500                   # Text chunk size for embeddings
CHUNK_OVERLAP=50                 # Overlap between chunks
AUTO_EMBED=true                  # Auto-add new transcripts

# Audio settings
AUDIO_QUALITY=high               # high/medium/low
SAMPLE_RATE=44100                # Audio sample rate
NOISE_REDUCTION=true             # Enable noise filtering

# Behavior settings
AUTO_ENHANCE=true                # Auto-enhance transcripts with Gemini
SESSION_NAMING=auto              # auto/manual session naming
EXPORT_FORMAT=markdown           # Default export format

# Custom command shortcuts (user control)
SHORTCUT_RECORD=rec              # Custom shortcut for 'dictate record'
SHORTCUT_SEARCH=s                # Custom shortcut for 'dictate search'
SHORTCUT_FIND=f                  # Custom shortcut for 'dictate find'
SHORTCUT_EMBED=e                 # Custom shortcut for 'dictate embed'
```


### Configuration File (~/.dictate/config.toml)
```toml
[audio]
quality = "high"
sample_rate = 44100
preferred_device = "default" # Robust fallback if unavailable
noise_reduction = true

[ai]
model = "gemini-pro"
embedding_model = "text-embedding-004"
auto_enhance = true
chunk_size = 500

[storage]
base_dir = "~/dictate"
auto_embed = true
max_sessions = 1000

[shortcuts]
# Custom command shortcuts - user has full control
record = "rec"          # 'rec' instead of 'dictate record'
search = "s"            # 's' instead of 'dictate search'  
find = "f"              # 'f' instead of 'dictate find'
embed = "e"             # 'e' instead of 'dictate embed'
list = "l"              # 'l' instead of 'dictate list'

[export]
default_format = "markdown"
include_metadata = true
template_dir = "~/.dictate/templates"
```

## 📁 File Organization

```
~/dictate/                       # User's dictate directory
├── config.toml                  # User configuration
├── sessions/                    # All recording sessions
│   ├── 20250904_143022_project_planning/
│   │   ├── audio.wav            # Original recording
│   │   ├── transcript.md        # Enhanced transcript
│   │   ├── metadata.json       # Session metadata
│   │   └── exports/             # Various export formats
│   └── 20250904_150315_meeting_notes/
├── vector_store/                # ChromaDB persistence
│   ├── chroma.sqlite3          # Vector database
│   └── embeddings/             # Embedding cache
├── templates/                   # Export templates
│   ├── markdown.md
│   ├── notion.json
│   └── obsidian.md
└── searches/                    # Saved search results
    └── voice_search_20250904.md
```

## 🚀 Getting Started (New User Experience)

### Step 1: Installation
```bash
# Simple git clone installation
git clone https://github.com/benjamayden/dictate.git
cd dictate
pip install -e .  # Installs dependencies + creates 'dictate' command
```

### Step 2: Setup
```bash
dictate setup
# Interactive wizard:
# 1. Enter Gemini API key
# 2. Choose audio device
# 3. Set preferences
# 4. Test recording
```

### Step 3: First Recording
```bash
# Full command
dictate record

# Or with custom alias (after setup-aliases)
rec  # If user set ALIAS_RECORD=rec

# Beautiful terminal interface guides user through first recording
```


### Step 4: Enable Embedding
```bash
dictate embed
# Builds initial semantic search index
```

## 🎨 User Experience Highlights


### Terminal Interface
- 🎨 Beautiful, colorful output using Rich
- 📊 Real-time audio level meters during recording
- ⏱️ Live transcription progress indicators
- 📋 Formatted transcript display with syntax highlighting
- ⚡ CLI help lists all shortcuts dynamically

### Smart Features
- 🤖 Auto-generated session names from content
- 🔍 Instant search across all transcripts
- 💡 Related content suggestions
- 📝 Automatic action item extraction
- 🏷️ Smart tagging and categorization
- 🧠 Unified 'embed' command for semantic search
- Robust microphone fallback (never blocks recording)

### Integration Ready
- 📁 Export to Markdown, Notion, Obsidian
- 🔗 API endpoints for custom integrations
- 📋 JSON export for programmatic access
- 🔄 Import from other transcription tools

## 📈 Performance Characteristics

### Startup Time
- **Cold start:** ~2 seconds (ChromaDB loading)
- **Warm start:** ~0.5 seconds (cached)

### Recording Performance
- **Audio latency:** <100ms (native PyAudio)
- **Transcription:** ~2-5 seconds per minute (Gemini API)
- **Vectorization:** ~1 second per transcript (local ChromaDB)

### Search Performance
- **Text search:** Instant (<100ms)
- **Vector search:** ~200-500ms for 1000+ transcripts
- **Voice search:** ~3-8 seconds (including transcription)

## 🔒 Privacy and Security

### Data Storage
- ✅ All audio and transcripts stored locally
- ✅ Vector embeddings stored locally (ChromaDB)
- ✅ Only text sent to Gemini API (not audio files)
- ✅ No cloud dependencies except Gemini API

### API Usage
- 🔐 API keys stored in local config only
- 📡 Minimal API calls (transcription + embeddings)
- 🚫 No audio files transmitted to cloud
- 🔒 All processing happens locally

## 🧪 Testing Strategy

### Unit Tests
- Audio recording/playback
- ChromaDB operations
- Gemini API integration
- Configuration management

### Integration Tests
- End-to-end recording workflows
- Search accuracy testing
- Cross-platform compatibility
- Performance benchmarking

### User Testing
- Setup experience on fresh systems
- CLI usability
- Search relevance quality
- Export functionality

## 📊 Success Metrics

### Technical Metrics
- Setup success rate >95%
- Recording failure rate <1%
- Search relevance score >0.8
- Startup time <3 seconds

### User Experience Metrics
- Time to first successful recording <2 minutes
- Daily active usage retention
- Feature adoption rates
- Support ticket volume

---

## 🎯 Implementation Priority

**Phase 1** (MVP): Core recording + transcription + basic search
**Phase 2** (CLI): Beautiful interface + configuration
**Phase 3** (Advanced): Document enhancement + exports
**Phase 4** (Polish): Packaging + distribution + integrations

This plan eliminates all Docker complexity while delivering a superior user experience with full vector search capabilities!
