#!/usr/bin/env python3
"""
Command Line Interface for Voice Dictation Tool

Beautiful CLI using Click and Rich for gorgeous terminal experience.
"""

import os
import sys
import subprocess
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


def create_session_folder(recordings_dir: Path) -> tuple[Path, str]:
    """Create a new session folder with timestamp."""
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
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


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """🎙️ Voice Dictation Tool with AI Search
    
    A powerful voice dictation tool that records audio, transcribes it using
    Google Gemini AI, and provides semantic search across all transcripts.
    """
    pass


@cli.command()
@click.option('--duration', '-d', type=int, help='Maximum recording duration in seconds')
@click.option('--output', '-o', help='Custom output filename (without extension)')
@click.option('--microphone', '-m', type=int, help='Microphone device index')
def record(duration: Optional[int], output: Optional[str], microphone: Optional[int]):
    """🎤 Record and transcribe audio
    
    Start recording audio from your microphone, then automatically transcribe
    it using Google Gemini AI. The audio and transcript are saved to the
    recordings directory.
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
                microphone = int(config['preferred_microphone'])
            except ValueError:
                pass
                
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
        session_dir, timestamp = create_session_folder(recordings_dir)
        
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
@click.option('--save', '-s', is_flag=True, help='Save results to file')
def search(query: str, limit: int, save: bool):
    """🔍 Search transcripts with text query
    
    Perform semantic search across all your transcripts using a text query.
    This requires that transcripts have been added to the vector store first.
    """
    config = load_config()
    recordings_dir = ensure_recordings_dir(config['recordings_dir'])
    
    try:
        # Initialize vector store
        vector_store = VectorStoreManager(recordings_dir / "vector_store")
        
        # Perform search
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🔍 Searching...", total=None)
            results = vector_store.search_similar(query, limit=limit)
            
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
                
            # Save results if requested
            if save:
                searches_dir = recordings_dir / "searches"
                result_file = vector_store.save_search_results(query, results, searches_dir)
                if result_file:
                    console.print(f"\n💾 Results saved to: [cyan]{result_file.name}[/cyan]")
                    
        else:
            console.print(f"❌ No results found for: [cyan]'{query}'[/cyan]")
            console.print("💡 Make sure transcripts are added to vector store with 'dictate vectorize'")
            
    except Exception as e:
        console.print(f"❌ [red]Search error: {e}[/red]")
        sys.exit(1)


@cli.command()
def vectorize():
    """⚡ Add transcripts to vector search index
    
    Process all transcript files and add them to the vector store for semantic search.
    This needs to be run before you can search transcripts.
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
        
        # Find transcript files
        transcript_files = list(recordings_dir.glob("*.md")) + list(recordings_dir.glob("*.txt"))
        
        if not transcript_files:
            console.print("❌ No transcript files found in recordings directory")
            console.print(f"📁 Looking in: {recordings_dir}")
            sys.exit(1)
            
        console.print(f"📚 Found {len(transcript_files)} transcript files")
        
        # Process each file
        success_count = 0
        
        with Progress(console=console) as progress:
            task = progress.add_task("⚡ Vectorizing transcripts...", total=len(transcript_files))
            
            for transcript_file in transcript_files:
                if vector_store.add_transcript(transcript_file, transcriber):
                    success_count += 1
                progress.advance(task)
                
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
