#!/usr/bin/env python3
"""
Transcription Module

Unified Gemini API integration for audio transcription and text embeddings.
"""

import os
from pathlib import Path
from typing import Optional, List, Union
from datetime import datetime
import mimetypes

try:
    from google import genai
except ImportError:
    genai = None


class GeminiTranscriber:
    """Unified Gemini API for transcription and embeddings."""
    
    def __init__(self, api_key: str):
        """Initialize the Gemini client.
        
        Args:
            api_key: Google Gemini API key
        """
        if genai is None:
            raise ImportError("Google GenAI not available. Install with: pip install google-genai")
            
        if not api_key or api_key == "your-api-key-here":
            raise ValueError("Valid Gemini API key required")
            
        self.api_key = api_key
        
        # Configure the client
        self.client = genai.Client(api_key=api_key)
        
        # Initialize models
        self.text_model_name = 'gemini-2.5-flash'
        # Use Gemini's latest text embedding model for all embedding operations
        self.embedding_model = 'models/text-embedding-004'
        
    def transcribe_audio(self, audio_path: Path) -> Optional[str]:
        """Convert audio to text using Gemini.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            if not audio_path.exists():
                print(f"Audio file not found: {audio_path}")
                return None
                
            # Check file type
            mime_type, _ = mimetypes.guess_type(str(audio_path))
            if not mime_type or not mime_type.startswith('audio/'):
                print(f"Invalid audio file type: {mime_type}")
                return None
                
            # Upload file to Gemini
            audio_file = self.client.files.upload(file=str(audio_path))
            
            # Create prompt for transcription
            prompt = """
Please transcribe this audio file accurately. Follow these guidelines:
1. Use proper punctuation and capitalization
2. Break into paragraphs where natural pauses occur
3. Use standard spelling (no phonetic spellings)
4. do not include timestamps they are not needed
5. Do not add any commentary or analysis - just the transcription

Transcription:
"""
            
            # Generate transcription
            response = self.client.models.generate_content(
                model=self.text_model_name,
                contents=[audio_file, prompt]
            )
            
            if response and response.text:
                transcription = response.text.strip()
                
                # Clean up the transcription
                transcription = self._clean_transcription(transcription)
                
                # Delete the uploaded file from Gemini
                try:
                    self.client.files.delete(name=audio_file.name)
                except:
                    pass  # Ignore cleanup errors
                    
                return transcription
            else:
                print("No transcription received from Gemini")
                return None
                
        except Exception as e:
            print(f"Transcription error: {e}")
            return None
            
    def _clean_transcription(self, text: str) -> str:
        """Clean up transcription text.
        
        Args:
            text: Raw transcription text
            
        Returns:
            Cleaned transcription text
        """
        # Remove common transcription artifacts
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and common prefixes
            if not line:
                continue
            if line.lower().startswith(('transcription:', 'transcript:', 'audio transcription:')):
                continue
                
            cleaned_lines.append(line)
            
        return '\n\n'.join(cleaned_lines)
        
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get text embedding using Gemini.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            if not text.strip():
                return None
                
            # Generate embedding
            result = self.client.models.embed_content(
                model=self.embedding_model,
                contents=[text]
            )
            
            if result and hasattr(result, 'embeddings') and result.embeddings:
                # Extract the embedding values from the first embedding in the response
                embedding = result.embeddings[0]
                if hasattr(embedding, 'values') and embedding.values:
                    return list(embedding.values)
                else:
                    print("No embedding values found")
                    return None
            else:
                print("No embedding received from Gemini")
                return None
                
        except Exception as e:
            print(f"Embedding error: {e}")
            return None
            
    def enhance_transcript(self, text: str, audio_path: Optional[Path] = None) -> str:
        """Add formatting, structure, and enhancement to transcript.
        
        Args:
            text: Raw transcript text
            audio_path: Optional path to original audio file for context
            
        Returns:
            Enhanced transcript with better formatting
        """
        try:
            # Create enhancement prompt
            prompt = f"""
Please enhance this transcript by:
1. Adding proper formatting and structure
2. Breaking into logical paragraphs and sections
3. Adding appropriate headings where topics change
4. Correcting any obvious transcription errors
5. Improving readability while maintaining the original meaning
6. Adding a brief summary at the top if the content is substantial

Original transcript:
{text}

Enhanced transcript:
"""
            
            response = self.client.models.generate_content(
                model=self.text_model_name,
                contents=prompt
            )
            
            if response and response.text:
                enhanced = response.text.strip()
                
                # Add metadata header
                metadata_header = self._generate_metadata_header(text, audio_path)
                
                return f"{metadata_header}\n\n{enhanced}"
            else:
                # Return original with basic metadata if enhancement fails
                metadata_header = self._generate_metadata_header(text, audio_path)
                return f"{metadata_header}\n\n{text}"
                
        except Exception as e:
            print(f"Enhancement error: {e}")
            # Return original with basic metadata
            metadata_header = self._generate_metadata_header(text, audio_path)
            return f"{metadata_header}\n\n{text}"
            
    def _generate_metadata_header(self, text: str, audio_path: Optional[Path] = None) -> str:
        """Generate metadata header for transcript.
        
        Args:
            text: Transcript text
            audio_path: Optional path to audio file
            
        Returns:
            Formatted metadata header
        """
        lines = text.split('\n')
        word_count = len(text.split())
        char_count = len(text)
        
        header_lines = [
            "# Voice Transcript",
            "",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Words:** {word_count}",
            f"**Characters:** {char_count}",
            f"**Lines:** {len([l for l in lines if l.strip()])}",
        ]
        
        if audio_path:
            header_lines.append(f"**Source Audio:** {audio_path.name}")
            
        header_lines.extend([
            "",
            "---",
        ])
        
        return '\n'.join(header_lines)
        
    def extract_action_items(self, text: str) -> List[str]:
        """Extract action items and tasks from transcript.
        
        Args:
            text: Transcript text
            
        Returns:
            List of action items
        """
        try:
            prompt = f"""
Analyze this transcript and extract any action items, tasks, or next steps mentioned.
Return them as a simple bulleted list, one item per line.
If no action items are found, return "No action items identified."

Transcript:
{text}

Action items:
"""
            
            response = self.client.models.generate_content(
                model=self.text_model_name,
                contents=prompt
            )
            
            if response and response.text:
                action_text = response.text.strip()
                
                if "no action items" in action_text.lower():
                    return []
                    
                # Parse bulleted list
                lines = action_text.split('\n')
                action_items = []
                
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                        # Remove bullet and clean up
                        item = line[1:].strip()
                        if item:
                            action_items.append(item)
                            
                return action_items
            else:
                return []
                
        except Exception as e:
            print(f"Action item extraction error: {e}")
            return []
            
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate a concise summary of the transcript.
        
        Args:
            text: Transcript text
            max_length: Maximum summary length in words
            
        Returns:
            Summary text
        """
        try:
            prompt = f"""
Create a concise summary of this transcript in {max_length} words or less.
Focus on the main topics, key decisions, and important information.

Transcript:
{text}

Summary:
"""
            
            response = self.client.models.generate_content(
                model=self.text_model_name,
                contents=prompt
            )
            
            if response and response.text:
                summary = response.text.strip()
                
                # Ensure summary isn't too long
                words = summary.split()
                if len(words) > max_length:
                    summary = ' '.join(words[:max_length]) + '...'
                    
                return summary
            else:
                return "Summary generation failed."
                
        except Exception as e:
            print(f"Summary generation error: {e}")
            return f"Summary error: {e}"
            
    def categorize_transcript(self, text: str) -> List[str]:
        """Automatically categorize the transcript content.
        
        Args:
            text: Transcript text
            
        Returns:
            List of category tags
        """
        try:
            prompt = f"""
Analyze this transcript and suggest 2-5 category tags that best describe the content.
Choose from common categories like: meeting, brainstorm, interview, lecture, notes, 
personal, work, project, technical, creative, planning, decision, etc.

Return only the category words, separated by commas.

Transcript:
{text}

Categories:
"""
            
            response = self.client.models.generate_content(
                model=self.text_model_name,
                contents=prompt
            )
            
            if response and response.text:
                categories_text = response.text.strip()
                
                # Parse comma-separated categories
                categories = [cat.strip().lower() for cat in categories_text.split(',')]
                categories = [cat for cat in categories if cat and len(cat) > 1]
                
                return categories[:5]  # Limit to 5 categories
            else:
                return []
                
        except Exception as e:
            print(f"Categorization error: {e}")
            return []
