#!/usr/bin/env python3
"""
Command Line Interface for Voice Dictation Tool

Beautiful CLI using Click and Rich for gorgeous terminal experience.
"""

# Suppress warnings before any imports
import warnings
warnings.filterwarnings("ignore", message=".*urllib3.*OpenSSL.*")
warnings.filterwarnings("ignore", category=UserWarning)

import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table
from rich import print as rprint

# Suppress verbose ChromaDB logging and SSL warnings
logging.getLogger("chromadb").setLevel(logging.ERROR)
logging.getLogger("onnxruntime").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
# Suppress urllib3 SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

# Import our modules
from .audio_recorder import AudioRecorder
from .transcription import GeminiTranscriber
from .vector_store import VectorStoreManager

console = Console()


def load_config() -> dict:
    """Load configuration from environment variables."""
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        'api_key': os.getenv('GEMINI_API_KEY'),
        'recordings_dir': os.getenv('DICTATE_RECORDINGS_DIR', './recordings'),
        'alias_name': os.getenv('DICTATE_ALIAS_NAME', 'dictate'),
        'command_alias': os.getenv('DICTATE_COMMAND_ALIAS', 'dictate'),
        'folder_alias': os.getenv('NOTES_FOLDER_ALIAS', 'vnotes'),
        'preferred_microphone': os.getenv('PREFERRED_MICROPHONE'),
        'transcript_format': os.getenv('TRANSCRIPT_FORMAT', 'md'),
        'auto_open_transcript': os.getenv('AUTO_OPEN_TRANSCRIPT', 'true').lower() == 'true',
    }
    
    return config


def ensure_recordings_dir(recordings_dir: str) -> Path:
    """Ensure recordings directory exists."""
    path = Path(recordings_dir).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_session_folder(recordings_dir: Path, no_vectorize: bool = False) -> tuple[Path, str]:
    """Create a new session folder with timestamp."""
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    if no_vectorize:
        timestamp += "_nv"
    session_dir = recordings_dir / timestamp
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir, timestamp


def open_file_in_editor(file_path: Path):
    """Open file in default editor or viewer."""
    try:
        if sys.platform == 'darwin':  # macOS
            subprocess.run(['open', str(file_path)], check=True)
        elif sys.platform.startswith('linux'):  # Linux
            subprocess.run(['xdg-open', str(file_path)], check=True)
        elif sys.platform == 'win32':  # Windows
            subprocess.run(['start', str(file_path)], shell=True, check=True)
        else:
            console.print(f"📄 File saved: {file_path}")
    except Exception as e:
        console.print(f"⚠️  Could not open file automatically: {e}")
        console.print(f"📄 File saved: {file_path}")


def get_shortcuts_help() -> str:
    """Get the current shortcuts for help display."""
    try:
        config = load_config()
        record_alias = config.get('alias_name', 'rec')
        command_alias = config.get('command_alias', 'dictate')
        folder_alias = config.get('folder_alias', 'vnotes')
        
        return f"""
    🚀 Quick Shortcuts (configured in setup):
    • {record_alias}        = dictate record
    • {record_alias} -nv    = dictate record --no-vectorize  
    • {folder_alias}     = open recordings folder
    • {command_alias}    = dictate (main command shortcut)
    """
    except:
        return """
    🚀 Quick Shortcuts (configured in setup):
    • rec        = dictate record
    • rec -nv    = dictate record --no-vectorize  
    • vnotes     = open recordings folder
    • dictate    = dictate (main command shortcut)
    """


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """🎙️ Voice Dictation Tool with AI Search
    
    A powerful voice dictation tool that records audio, transcribes it using
    Google Gemini AI, and provides semantic search across all transcripts.
    
    💡 Use 'dictate shortcuts' to see your configured shell shortcuts.
    """
    pass


@cli.command()
def shortcuts():
    """🚀 Show configured command shortcuts
    
    Display the current shell shortcuts configured during setup.
    """
    console.print(get_shortcuts_help())


@cli.command()
@click.option('--duration', '-d', type=int, help='Maximum recording duration in seconds')
@click.option('--output', '-o', help='Custom output filename (without extension)')
@click.option('--microphone', '-m', type=int, help='Microphone device index')
@click.option('--no-vectorize', '-nv', is_flag=True, help='Skip vectorization for this recording (adds _nv suffix)')
def record(duration: Optional[int], output: Optional[str], microphone: Optional[int], no_vectorize: bool):
    """🎤 Record and transcribe audio
    
    Start recording audio from your microphone, then automatically transcribe
    it using Google Gemini AI. The audio and transcript are saved to the
    recordings directory.
    
    Use --no-vectorize to skip this recording when building the search index.
    """
    config = load_config()
    
    if not config['api_key'] or config['api_key'] == 'your-api-key-here':
        console.print("❌ [red]Gemini API key not configured![/red]")
        console.print("Please set your API key in the .env file")
        sys.exit(1)
        
    recordings_dir = ensure_recordings_dir(config['recordings_dir'])
    
    try:
        # Initialize components
        recorder = AudioRecorder()
        transcriber = GeminiTranscriber(config['api_key'])
        
        # Select microphone
        if microphone is None and config['preferred_microphone']:
            try:
                preferred_mic = int(config['preferred_microphone'])
                # Validate that the preferred microphone actually exists
                available_mics = recorder.get_available_microphones()
                if any(mic['index'] == preferred_mic for mic in available_mics):
                    microphone = preferred_mic
                else:
                    console.print(f"⚠️ [yellow]Preferred microphone {preferred_mic} not available, selecting automatically[/yellow]")
            except (ValueError, Exception):
                console.print(f"⚠️ [yellow]Invalid preferred microphone setting, selecting automatically[/yellow]")
                
        if microphone is None:
            try:
                microphone = recorder.select_microphone()
            except RuntimeError as e:
                console.print(f"❌ [red]Microphone error: {e}[/red]")
                sys.exit(1)
                
        # Show microphone info
        mics = recorder.get_available_microphones()
        selected_mic = next((m for m in mics if m['index'] == microphone), None)
        if selected_mic:
            console.print(f"🎤 Using microphone: [cyan]{selected_mic['name']}[/cyan]")
        
        # Start recording
        console.print("\n[green]🔴 Recording started...[/green]")
        console.print("Press [bold]Enter[/bold] to stop recording")
        
        try:
            recorder.start_recording(microphone)
            
            # Simple input wait - just like the original
            input()  # Wait for user to press Enter
            
        except KeyboardInterrupt:
            console.print("\n⏹️  Recording stopped by user")
            
        # Stop recording and save
        console.print("⏹️  Recording stopped")
        
        # Create session folder for organized storage
        session_dir, timestamp = create_session_folder(recordings_dir, no_vectorize)
        
        if output:
            if not output.endswith('.wav'):
                output += '.wav'
            audio_filename = output
        else:
            audio_filename = f"{timestamp}.wav"
            
        audio_path = session_dir / audio_filename
        final_audio_path = recorder.stop_recording(str(audio_path))
        audio_file = Path(final_audio_path)
        
        if not audio_file.exists():
            console.print("❌ [red]Failed to save recording[/red]")
            sys.exit(1)
            
        console.print(f"✅ Audio saved: [cyan]{session_dir.name}/{audio_file.name}[/cyan]")
        
        # Transcribe audio
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🤖 Transcribing audio...", total=None)
            
            transcript = transcriber.transcribe_audio(audio_file)
            
        if transcript:
            # Determine transcript format and path
            file_extension = config['transcript_format']
            if file_extension not in ['txt', 'md']:
                file_extension = 'md'  # default to markdown
                
            transcript_path = audio_file.with_suffix(f'.{file_extension}')
            
            # Save transcript based on format
            if file_extension == 'md':
                enhanced_transcript = transcriber.enhance_transcript(transcript, audio_file)
                content = enhanced_transcript
            else:
                # For txt format, just use clean transcript without markdown formatting
                content = transcript
            
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            console.print(f"✅ Transcript saved: [cyan]{session_dir.name}/{transcript_path.name}[/cyan]")
            
            # Show transcript preview
            if file_extension == 'md':
                lines = content.split('\n')
                preview_lines = [line for line in lines if line.strip() and not line.startswith('#')][:5]
                preview = '\n'.join(preview_lines[:3])
            else:
                preview = content[:300] + "..." if len(content) > 300 else content
                
            panel = Panel(
                preview,
                title="📄 Transcript Preview",
                border_style="green"
            )
            console.print(panel)
            
            # Ask if user wants to open the transcript
            if config['auto_open_transcript']:
                if Confirm.ask("📖 Open transcript file?", default=True):
                    open_file_in_editor(transcript_path)
            
            # Ask if user wants to vectorize this transcript for search (only if not marked as no-vectorize)
            if not no_vectorize:
                if Confirm.ask("⚡ Add this transcript to search index?", default=True):
                    console.print("🔍 Adding transcript to search index...")
                    
                    try:
                        vector_store = VectorStoreManager(recordings_dir / "vector_store")
                        
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            console=console
                        ) as progress:
                            task = progress.add_task("⚡ Vectorizing...", total=None)
                            
                            if vector_store.add_transcript(transcript_path, transcriber):
                                console.print("✅ [green]Transcript added to search index[/green]")
                                console.print("💡 You can now search for this content with 'dictate search' or 'dictate find'")
                            else:
                                console.print("⚠️ [yellow]Failed to add transcript to search index[/yellow]")
                                
                    except Exception as e:
                        console.print(f"⚠️ [yellow]Could not add to search index: {e}[/yellow]")
                        console.print("💡 You can manually add it later with 'dictate embed'")
                else:
                    # User chose not to vectorize, rename folder to add _nv suffix
                    try:
                        new_session_dir = session_dir.parent / (session_dir.name + "_nv")
                        session_dir.rename(new_session_dir)
                        console.print(f"📁 [yellow]Folder marked as no-vectorize: {new_session_dir.name}[/yellow]")
                        console.print("💡 This recording will be excluded from search indexing")
                    except Exception as e:
                        console.print(f"⚠️ [yellow]Could not rename folder: {e}[/yellow]")
            
        else:
            console.print("❌ [red]Transcription failed[/red]")
            
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('audio_file', type=click.Path(exists=True))
def transcribe(audio_file):
    """📝 Transcribe an existing audio file
    
    Transcribe an audio file that you already have, without recording new audio.
    """
    config = load_config()
    
    if not config['api_key'] or config['api_key'] == 'your-api-key-here':
        console.print("❌ [red]Gemini API key not configured![/red]")
        sys.exit(1)
        
    audio_path = Path(audio_file)
    
    try:
        transcriber = GeminiTranscriber(config['api_key'])
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🤖 Transcribing audio...", total=None)
            transcript = transcriber.transcribe_audio(audio_path)
            
        if transcript:
            # Determine transcript format and path
            file_extension = config['transcript_format']
            if file_extension not in ['txt', 'md']:
                file_extension = 'md'  # default to markdown
                
            transcript_path = audio_path.with_suffix(f'.{file_extension}')
            
            # Save transcript based on format
            if file_extension == 'md':
                enhanced_transcript = transcriber.enhance_transcript(transcript, audio_path)
                content = enhanced_transcript
            else:
                # For txt format, just use clean transcript without markdown formatting
                content = transcript
            
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            console.print(f"✅ Transcript saved: [cyan]{transcript_path.name}[/cyan]")
            
            # Show transcript
            panel = Panel(
                content,
                title="📄 Transcript",
                border_style="green"
            )
            console.print(panel)
            
            # Ask if user wants to open the transcript
            if config['auto_open_transcript']:
                if Confirm.ask("📖 Open transcript file?", default=True):
                    open_file_in_editor(transcript_path)
            
        else:
            console.print("❌ [red]Transcription failed[/red]")
            
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('query')
@click.option('--limit', '-l', default=5, help='Maximum number of results')
def search(query: str, limit: int):
    """🔍 Search transcripts with text query
    
    Perform semantic search across all your transcripts using a text query.
    Results are automatically saved to searches/ folder as txt files.
    This requires that transcripts have been added to the vector store first.
    """
    config = load_config()
    recordings_dir = ensure_recordings_dir(config['recordings_dir'])
    
    try:
        # Initialize vector store and transcriber for consistent embeddings
        vector_store = VectorStoreManager(recordings_dir / "vector_store")
        transcriber = GeminiTranscriber(config['api_key']) if config['api_key'] and config['api_key'] != 'your-api-key-here' else None
        
        # Perform search
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🔍 Searching...", total=None)
            results = vector_store.search_similar(query, limit=limit, transcriber=transcriber)
            
        if results:
            console.print(f"\n🎯 Found {len(results)} results for: [cyan]'{query}'[/cyan]\n")
            
            for i, result in enumerate(results, 1):
                metadata = result['metadata']
                similarity = result['similarity']
                
                # Create result panel
                content = result['content']
                if len(content) > 300:
                    content = content[:300] + "..."
                    
                header = f"📄 {metadata.get('file_name', 'Unknown')} (Similarity: {similarity:.3f})"
                
                panel = Panel(
                    content,
                    title=header,
                    border_style="blue"
                )
                console.print(panel)
                
            # Always save search results to searches/ folder
            searches_dir = recordings_dir / "searches"
            result_file = vector_store.save_search_results(query, results, searches_dir, config['transcript_format'])
            if result_file:
                console.print(f"\n💾 Search results saved to: [cyan]{result_file.name}[/cyan]")
                    
        else:
            console.print(f"❌ No results found for: [cyan]'{query}'[/cyan]")
            console.print("💡 Make sure transcripts are added to vector store with 'dictate embed'")
            
    except Exception as e:
        console.print(f"❌ [red]Search error: {e}[/red]")
        sys.exit(1)


@cli.command()
def embed():
    """⚡ Add transcripts to vector search index
    
    Process all transcript files and add them to the vector store for semantic search.
    This needs to be run before you can search transcripts.
    
    Note: 
    - Folders ending with '_nv' are skipped (no-vectorize)
    - Folders ending with '_v' are skipped (already vectorized)
    - Successfully vectorized folders get '_v' suffix added
    """
    config = load_config()
    
    if not config['api_key'] or config['api_key'] == 'your-api-key-here':
        console.print("❌ [red]Gemini API key not configured![/red]")
        sys.exit(1)
        
    recordings_dir = ensure_recordings_dir(config['recordings_dir'])
    
    try:
        # Initialize components
        transcriber = GeminiTranscriber(config['api_key'])
        vector_store = VectorStoreManager(recordings_dir / "vector_store")
        
        # Find transcript files (both loose files and in session folders)
        transcript_files = []
        
        # Look for loose transcript files in root
        transcript_files.extend(recordings_dir.glob("*.md"))
        transcript_files.extend(recordings_dir.glob("*.txt"))
        
        # Look for transcript files in session folders
        for item in recordings_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Skip special directories
                if item.name in ['vector_store', 'searches']:
                    continue
                # Skip folders marked as no-vectorize (ending with _nv)
                if item.name.endswith('_nv'):
                    continue
                # Skip folders already vectorized (ending with _v) unless they have new content
                if item.name.endswith('_v'):
                    continue
                transcript_files.extend(item.glob("*.md"))
                transcript_files.extend(item.glob("*.txt"))
        
        if not transcript_files:
            console.print("❌ No transcript files found in recordings directory")
            console.print(f"📁 Looking in: {recordings_dir}")
            console.print("💡 Make sure you have recorded and transcribed some audio first")
            sys.exit(1)
            
        console.print(f"📚 Found {len(transcript_files)} transcript files")
        
        # Process each file and track which folders were processed
        success_count = 0
        processed_folders = set()
        
        with Progress(console=console) as progress:
            task = progress.add_task("⚡ Vectorizing transcripts...", total=len(transcript_files))
            
            for transcript_file in transcript_files:
                if vector_store.add_transcript(transcript_file, transcriber):
                    success_count += 1
                    # Track the parent folder for renaming
                    parent_folder = transcript_file.parent
                    if parent_folder != recordings_dir:  # Only track session folders, not root files
                        processed_folders.add(parent_folder)
                progress.advance(task)
        
        # Rename successfully vectorized folders to add _v suffix
        renamed_count = 0
        for folder in processed_folders:
            if not folder.name.endswith('_v') and not folder.name.endswith('_nv'):
                new_name = folder.name + '_v'
                new_path = folder.parent / new_name
                try:
                    folder.rename(new_path)
                    renamed_count += 1
                except Exception as e:
                    console.print(f"⚠️  Could not rename {folder.name}: {e}")
        
        if renamed_count > 0:
            console.print(f"📁 Renamed {renamed_count} folder(s) with _v suffix to mark as vectorized")
                
        console.print(f"\n✅ Successfully processed {success_count}/{len(transcript_files)} transcripts")
        
        # Show stats
        stats = vector_store.get_collection_stats()
        if 'error' not in stats:
            console.print(f"📊 Vector store stats:")
            console.print(f"   • Total chunks: {stats['total_chunks']}")
            console.print(f"   • Unique files: {stats['unique_files']}")
            console.print(f"   • Avg chunks per file: {stats['avg_chunks_per_file']:.1f}")
            
    except Exception as e:
        console.print(f"❌ [red]Vectorization error: {e}[/red]")
        sys.exit(1)


@cli.command(name='list')
@click.option('--days', '-d', default=7, help='Show recordings from last N days (default: 7)')
@click.option('--date', help='Show recordings around specific date (YYYY-MM-DD format)')
@click.option('--month', help='Show recordings for entire month (YYYY-MM format)')
def list_recordings(days: int, date: str, month: str):
    """📋 List recordings with smart date filtering
    
    By default shows last 7 days to avoid overwhelming output.
    Use --date to see recordings around a specific date (±2 days).
    Use --month to see all recordings in a month.
    """
    config = load_config()
    recordings_dir = ensure_recordings_dir(config['recordings_dir'])
    
    try:
        from datetime import datetime, timedelta
        import os
        
        # Collect all session directories
        session_dirs = []
        for item in recordings_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Try to parse timestamp from directory name
                parts = item.name.split('_')
                if len(parts) >= 2:
                    try:
                        date_part = parts[0]
                        time_part = parts[1]
                        # Parse format: DDMMYYYY_HHMMSS
                        if len(date_part) == 8 and len(time_part) == 6:
                            day = int(date_part[:2])
                            month_num = int(date_part[2:4])
                            year = int(date_part[4:8])
                            hour = int(time_part[:2])
                            minute = int(time_part[2:4])
                            second = int(time_part[4:6])
                            
                            session_date = datetime(year, month_num, day, hour, minute, second)
                            session_dirs.append({
                                'path': item,
                                'name': item.name,
                                'date': session_date,
                                'files': list(item.glob('*'))
                            })
                    except (ValueError, IndexError):
                        continue
        
        if not session_dirs:
            console.print("📋 No recordings found")
            console.print(f"📁 Looking in: {recordings_dir}")
            return
            
        # Sort by date (newest first)
        session_dirs.sort(key=lambda x: x['date'], reverse=True)
        
        # Filter based on options
        now = datetime.now()
        filtered_sessions = []
        
        if month:
            # Filter by month (YYYY-MM format)
            try:
                year, month_num = map(int, month.split('-'))
                filtered_sessions = [s for s in session_dirs 
                                   if s['date'].year == year and s['date'].month == month_num]
                title = f"📅 {datetime(year, month_num, 1).strftime('%B %Y')} ({len(filtered_sessions)} recordings)"
            except ValueError:
                console.print("❌ Invalid month format. Use YYYY-MM (e.g., 2025-09)")
                return
                
        elif date:
            # Filter around specific date (±2 days)
            try:
                target_date = datetime.strptime(date, '%Y-%m-%d')
                start_date = target_date - timedelta(days=2)
                end_date = target_date + timedelta(days=2)
                filtered_sessions = [s for s in session_dirs 
                                   if start_date <= s['date'] <= end_date]
                title = f"📅 Around {target_date.strftime('%B %d, %Y')} (±2 days) ({len(filtered_sessions)} recordings)"
            except ValueError:
                console.print("❌ Invalid date format. Use YYYY-MM-DD (e.g., 2025-09-04)")
                return
                
        else:
            # Default: last N days
            cutoff_date = now - timedelta(days=days)
            filtered_sessions = [s for s in session_dirs if s['date'] >= cutoff_date]
            title = f"📅 Last {days} days ({len(filtered_sessions)} recordings)"
        
        if not filtered_sessions:
            console.print(f"📋 No recordings found for the specified time period")
            return
            
        # Display results grouped by date
        console.print(f"\n{title}\n")
        
        current_date = None
        for session in filtered_sessions:
            session_date = session['date'].date()
            
            # Print date header if it's a new date
            if current_date != session_date:
                current_date = session_date
                console.print(f"[bold cyan]{session_date.strftime('%B %d, %Y')}[/bold cyan]")
            
            # Find audio and transcript files
            audio_files = [f for f in session['files'] if f.suffix.lower() in ['.wav', '.mp3', '.m4a']]
            transcript_files = [f for f in session['files'] if f.suffix.lower() in ['.md', '.txt']]
            
            # Calculate duration if possible
            duration_str = ""
            if audio_files:
                try:
                    # Get file size as rough duration estimate
                    size_mb = audio_files[0].stat().st_size / (1024 * 1024)
                    # Rough estimate: 1MB ≈ 1 minute for compressed audio
                    estimated_minutes = int(size_mb)
                    if estimated_minutes > 0:
                        duration_str = f" ({estimated_minutes}:{estimated_minutes%60:02d})"
                except:
                    pass
            
            # Create session name (remove timestamp prefix for display)
            display_name = '_'.join(session['name'].split('_')[2:]) if len(session['name'].split('_')) > 2 else "untitled"
            if not display_name:
                display_name = "recording"
                
            # Check if this session is marked as no-vectorize or vectorized
            status_marker = ""
            if session['name'].endswith('_nv'):
                status_marker = " [dim yellow](no-vectorize)[/dim yellow]"
            elif session['name'].endswith('_v'):
                status_marker = " [dim green](vectorized)[/dim green]"
                
            # Show session info
            status_icons = ""
            if audio_files:
                status_icons += "🎤"
            if transcript_files:
                status_icons += "📄"
                
            console.print(f"   {status_icons} [green]{display_name}[/green]{duration_str}{status_marker}")
            
    except Exception as e:
        console.print(f"❌ [red]Error listing recordings: {e}[/red]")


@cli.command()
@click.argument('session_name')
def show(session_name: str):
    """📄 Show transcript for a specific session
    
    Display the transcript content for a recording session.
    Use session name or timestamp (e.g., '04092025_155531' or partial match).
    """
    config = load_config()
    recordings_dir = ensure_recordings_dir(config['recordings_dir'])
    
    try:
        # Find matching session directory
        matching_dirs = []
        for item in recordings_dir.iterdir():
            if item.is_dir() and session_name in item.name:
                matching_dirs.append(item)
        
        if not matching_dirs:
            console.print(f"❌ No session found matching: [cyan]{session_name}[/cyan]")
            console.print("💡 Use 'dictate list' to see available sessions")
            return
            
        if len(matching_dirs) > 1:
            console.print(f"❌ Multiple sessions match '[cyan]{session_name}[/cyan]':")
            for dir_path in matching_dirs:
                console.print(f"   📁 {dir_path.name}")
            console.print("💡 Be more specific with the session name")
            return
            
        session_dir = matching_dirs[0]
        
        # Find transcript file
        transcript_files = list(session_dir.glob('*.md')) + list(session_dir.glob('*.txt'))
        
        if not transcript_files:
            console.print(f"❌ No transcript found in session: [cyan]{session_dir.name}[/cyan]")
            return
            
        transcript_file = transcript_files[0]  # Take the first one found
        
        # Read and display transcript
        with open(transcript_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Create panel with transcript
        panel = Panel(
            content,
            title=f"📄 {session_dir.name}/{transcript_file.name}",
            border_style="green"
        )
        console.print(panel)
        
        # Ask if user wants to open the file
        if config.get('auto_open_transcript', True):
            if Confirm.ask("📖 Open transcript file?", default=False):
                open_file_in_editor(transcript_file)
                
    except Exception as e:
        console.print(f"❌ [red]Error showing session: {e}[/red]")


@cli.command()
@click.argument('query', required=False)
@click.option('--limit', '-l', default=5, help='Maximum results to return')
def find(query: str, limit: int):
    """🗣️ Voice search your transcripts
    
    Record a voice query and search transcripts using speech.
    If no query provided, will record audio for search.
    """
    config = load_config()
    
    if not config['api_key'] or config['api_key'] == 'your-api-key-here':
        console.print("❌ [red]Gemini API key not configured![/red]")
        sys.exit(1)
        
    recordings_dir = ensure_recordings_dir(config['recordings_dir'])
    
    try:
        # Initialize transcriber for consistent embeddings
        transcriber = GeminiTranscriber(config['api_key'])
        search_query = query
        
        # If no text query provided, record audio
        if not search_query:
            console.print("🎤 [green]Voice Search Mode[/green]")
            console.print("Press [bold]Enter[/bold] to start recording your search query...")
            input()
            
            # Record search query
            recorder = AudioRecorder()
            
            # Get preferred microphone
            microphone = None
            if config.get('preferred_microphone'):
                try:
                    microphone = int(config['preferred_microphone'])
                except (ValueError, TypeError):
                    pass
                    
            console.print("\n[green]🔴 Recording search query...[/green]")
            console.print("Press [bold]Enter[/bold] to stop recording")
            
            # Start recording
            recorder.start_recording(microphone)
            input()  # Wait for user to press Enter
            
            # Save temporary audio file
            temp_audio = recordings_dir / "temp_search_query.wav"
            final_audio_path = recorder.stop_recording(str(temp_audio))
            audio_file = Path(final_audio_path)
            
            console.print("⏹️  Recording stopped")
            
            # Transcribe the search query
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("🤖 Processing voice query...", total=None)
                search_query = transcriber.transcribe_audio(audio_file)
                
            # Clean up temp file
            if audio_file.exists():
                audio_file.unlink()
                
            if not search_query:
                console.print("❌ [red]Could not understand voice query[/red]")
                return
                
            console.print(f"🎯 Searching for: [cyan]'{search_query.strip()}'[/cyan]\n")
        
        # Perform the search
        vector_store = VectorStoreManager(recordings_dir / "vector_store")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🔍 Searching...", total=None)
            results = vector_store.search_similar(search_query, limit=limit, transcriber=transcriber)
            
        if results:
            console.print(f"🎯 Found {len(results)} results:\n")
            
            for i, result in enumerate(results, 1):
                metadata = result['metadata']
                similarity = result['similarity']
                
                content = result['content']
                if len(content) > 300:
                    content = content[:300] + "..."
                    
                header = f"📄 {metadata.get('file_name', 'Unknown')} (Similarity: {similarity:.3f})"
                
                panel = Panel(
                    content,
                    title=header,
                    border_style="blue"
                )
                console.print(panel)
                
            # Save search results
            searches_dir = recordings_dir / "searches"
            result_file = vector_store.save_search_results(search_query, results, searches_dir, config['transcript_format'])
            if result_file:
                console.print(f"\n💾 Search results saved to: [cyan]{result_file.name}[/cyan]")
                
        else:
            console.print(f"❌ No results found for: [cyan]'{search_query}'[/cyan]")
            console.print("💡 Make sure transcripts are added to vector store with 'dictate embed'")
            
    except Exception as e:
        console.print(f"❌ [red]Voice search error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--details', '-d', is_flag=True, help='Show detailed information about stored documents')
def inspect(details):
    """🔍 Inspect the ChromaDB vector store
    
    View information about your vector store including document count and samples.
    Use --details flag to see sample documents and metadata.
    """
    config = load_config()
    recordings_dir = ensure_recordings_dir(config['recordings_dir'])
    
    try:
        vector_store = VectorStoreManager(recordings_dir / "vector_store")
        
        # Check if vector store exists and has data
        stats = vector_store.get_collection_stats()
        
        if 'error' in stats:
            console.print("❌ No vector store found or empty")
            console.print("💡 Run 'dictate embed' to create index from your transcripts")
            return
            
        console.print(f"\n📊 Vector Store Status:")
        console.print(f"   📁 Location: {recordings_dir / 'vector_store'}")
        console.print(f"   📝 Total chunks: {stats['total_chunks']}")
        console.print(f"   📄 Unique files: {stats['unique_files']}")
        console.print(f"   📊 Avg chunks per file: {stats['avg_chunks_per_file']:.1f}")
        
        if details and stats['total_chunks'] > 0:
            console.print(f"\n📋 Sample documents:")
            
            # Get some sample data
            collection = vector_store.collection
            results = collection.get(limit=3, include=['documents', 'metadatas'])
            
            for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                filename = metadata.get('file_name', 'Unknown')
                preview = doc[:150] + "..." if len(doc) > 150 else doc
                
                panel = Panel(
                    preview,
                    title=f"📄 {filename}",
                    border_style="blue"
                )
                console.print(panel)
                
    except Exception as e:
        console.print(f"❌ [red]Error inspecting vector store: {e}[/red]")


@cli.command()
@click.confirmation_option(prompt='🗑️ Are you sure you want to completely wipe the vector store? This cannot be undone.')
def reset_vectors():
    """🗑️ Reset the ChromaDB vector store
    
    Completely wipe the vector store and start fresh. 
    You'll need to run 'dictate embed' again to rebuild the index.
    """
    config = load_config()
    recordings_dir = ensure_recordings_dir(config['recordings_dir'])
    
    try:
        import shutil
        vector_store_path = recordings_dir / "vector_store"
        
        # First, remove _v suffixes from folders since they won't be vectorized anymore
        renamed_count = 0
        for item in recordings_dir.iterdir():
            if item.is_dir() and item.name.endswith('_v'):
                new_name = item.name[:-2]  # Remove _v suffix
                new_path = item.parent / new_name
                try:
                    item.rename(new_path)
                    renamed_count += 1
                except Exception as e:
                    console.print(f"⚠️  Could not rename {item.name}: {e}")
        
        if renamed_count > 0:
            console.print(f"📁 Removed _v suffix from {renamed_count} folder(s)")
        
        # Then wipe the vector store
        if vector_store_path.exists():
            shutil.rmtree(vector_store_path)
            console.print("✅ [green]Vector store wiped successfully[/green]")
            console.print("💡 Run 'dictate embed' to rebuild index from your transcripts")
        else:
            console.print("ℹ️ Vector store was already empty")
            
    except Exception as e:
        console.print(f"❌ [red]Error resetting vector store: {e}[/red]")


@cli.command()
def list_mics():
    """🎤 List available microphones
    
    Show all available microphone devices with their details.
    """
    try:
        recorder = AudioRecorder()
        microphones = recorder.get_available_microphones()
        
        if not microphones:
            console.print("❌ No microphones found")
            return
            
        table = Table(title="🎤 Available Microphones")
        table.add_column("Index", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Channels", style="yellow")
        table.add_column("Sample Rate", style="blue")
        table.add_column("Host API", style="magenta")
        
        for mic in microphones:
            table.add_row(
                str(mic['index']),
                mic['name'],
                str(mic['channels']),
                f"{mic['sample_rate']:.0f} Hz",
                mic['hostapi']
            )
            
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ [red]Error listing microphones: {e}[/red]")


@cli.command()
@click.argument('session_name')
def remove(session_name: str):
    """🗑️ Remove transcript from vector search index
    
    Remove a specific transcript file and all its chunks from the vector store.
    Use session name or timestamp (e.g., '04092025_155531' or partial match).
    """
    config = load_config()
    recordings_dir = ensure_recordings_dir(config['recordings_dir'])
    
    try:
        # Find matching session directory
        matching_dirs = []
        for item in recordings_dir.iterdir():
            if item.is_dir() and session_name in item.name:
                matching_dirs.append(item)
        
        if not matching_dirs:
            console.print(f"❌ No session found matching: [cyan]{session_name}[/cyan]")
            console.print("💡 Use 'dictate list' to see available sessions")
            return
            
        if len(matching_dirs) > 1:
            console.print(f"❌ Multiple sessions match '[cyan]{session_name}[/cyan]':")
            for dir_path in matching_dirs:
                console.print(f"   📁 {dir_path.name}")
            console.print("💡 Please be more specific")
            return
            
        session_dir = matching_dirs[0]
        
        # Find transcript files in the session
        transcript_files = list(session_dir.glob('*.md')) + list(session_dir.glob('*.txt'))
        
        if not transcript_files:
            console.print(f"❌ No transcript files found in session: [cyan]{session_dir.name}[/cyan]")
            return
            
        # Initialize vector store
        vector_store = VectorStoreManager(recordings_dir / "vector_store")
        
        # Try to find transcripts in vector store that match this session
        # We need to be flexible since folder names may have changed (_v suffix added)
        session_base_name = session_dir.name.replace('_v', '').replace('_nv', '')
        
        removed_count = 0
        for transcript_file in transcript_files:
            # Try the current path first
            if vector_store.remove_transcript(transcript_file):
                removed_count += 1
            else:
                # Try with the original path (before _v suffix was added)
                original_name = transcript_file.name.replace('.txt', '').replace('.md', '')
                original_folder = recordings_dir / session_base_name
                original_transcript = original_folder / transcript_file.name
                if vector_store.remove_transcript(original_transcript):
                    removed_count += 1
                
        if removed_count > 0:
            console.print(f"✅ [green]Removed {removed_count} transcript(s) from search index[/green]")
            
            # Remove _v suffix if the folder has it (since it's no longer vectorized)
            if session_dir.name.endswith('_v'):
                new_name = session_dir.name[:-2]  # Remove _v suffix
                new_path = session_dir.parent / new_name
                session_dir.rename(new_path)
                console.print(f"📁 Renamed folder: {session_dir.name} → {new_name}")
        else:
            console.print("❌ No transcripts were found in the vector store to remove")
            
    except Exception as e:
        console.print(f"❌ [red]Error removing transcript: {e}[/red]")


@cli.command()
def config():
    """⚙️ Show current configuration
    
    Display the current configuration settings.
    """
    config_data = load_config()
    
    table = Table(title="⚙️ Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in config_data.items():
        if key == 'api_key':
            # Mask API key for security
            if value and value != 'your-api-key-here':
                display_value = f"{value[:8]}..." if len(value) > 8 else "Set"
            else:
                display_value = "❌ Not set"
        else:
            display_value = str(value) if value else "❌ Not set"
            
        table.add_row(key.replace('_', ' ').title(), display_value)
        
    console.print(table)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
