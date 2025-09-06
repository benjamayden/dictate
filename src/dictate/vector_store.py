#!/usr/bin/env python3
"""
Vector Store Management Module

Persistent vector store using ChromaDB for semantic search across transcripts.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None


class VectorStoreManager:
    """Persistent vector store using ChromaDB for semantic search."""
    
    def __init__(self, persist_directory: str = "./recordings/vector_store"):
        """Initialize the vector store.
        
        Args:
            persist_directory: Directory to store the ChromaDB database
        """
        if chromadb is None:
            raise ImportError("ChromaDB not available. Install with: pip install chromadb")
            
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection for transcripts
        # Note: We provide embeddings manually via Gemini, so we don't need ChromaDB's default embedding function
        self.collection = self.client.get_or_create_collection(
            name="transcripts",
            metadata={
                "description": "Voice dictation transcripts with semantic search",
                "embedding_model": "gemini-text-embedding-004",
                "embedding_provider": "google-gemini"
            }
        )
        
    def chunk_text(self, text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks for better search.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum characters per chunk
            chunk_overlap: Characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
            
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at word boundaries
            if end < len(text):
                # Look for the last space before the chunk limit
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
                    
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
                
            # Move start position with overlap
            start = end - chunk_overlap
            if start <= 0:
                start = end
                
        return chunks
        
    def add_transcript(self, transcript_path: Path, transcriber=None) -> bool:
        """Add a transcript to the vector store.
        
        Args:
            transcript_path: Path to the transcript file
            transcriber: Optional transcriber instance for generating embeddings
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read transcript content
            if not transcript_path.exists():
                print(f"Transcript file not found: {transcript_path}")
                return False
                
            with open(transcript_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if not content:
                print(f"Empty transcript file: {transcript_path}")
                return False
                
            # Generate unique ID for this transcript
            file_id = str(transcript_path.absolute())
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Check if already exists and unchanged
            existing = self.collection.get(ids=[file_id])
            if existing['ids'] and existing['metadatas']:
                existing_hash = existing['metadatas'][0].get('content_hash')
                if existing_hash == content_hash:
                    print(f"Transcript already up to date: {transcript_path.name}")
                    return True
                    
            # Chunk the text
            chunks = self.chunk_text(content)
            
            # Generate embeddings if transcriber is available
            embeddings = None
            if transcriber and hasattr(transcriber, 'get_embedding'):
                try:
                    embeddings = []
                    for chunk in chunks:
                        embedding = transcriber.get_embedding(chunk)
                        embeddings.append(embedding)
                except Exception as e:
                    print(f"Failed to generate embeddings: {e}")
                    embeddings = None
                    
            # Prepare data for ChromaDB
            chunk_ids = [f"{file_id}_{i}" for i in range(len(chunks))]
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                metadata = {
                    'source_file': str(transcript_path),
                    'file_name': transcript_path.name,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'content_hash': content_hash,
                    'added_date': datetime.now().isoformat(),
                    'chunk_length': len(chunk)
                }
                metadatas.append(metadata)
                
            # Add to collection
            if embeddings:
                self.collection.upsert(
                    ids=chunk_ids,
                    documents=chunks,
                    metadatas=metadatas,
                    embeddings=embeddings
                )
            else:
                self.collection.upsert(
                    ids=chunk_ids,
                    documents=chunks,
                    metadatas=metadatas
                )
                
            print(f"Added transcript: {transcript_path.name} ({len(chunks)} chunks)")
            return True
            
        except Exception as e:
            print(f"Error adding transcript {transcript_path}: {e}")
            return False
            
    def search_similar(self, query: str, limit: int = 5, threshold: float = 0.0, transcriber=None) -> List[Dict[str, Any]]:
        """Perform semantic search across all transcripts.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0.0 to 1.0)
            transcriber: GeminiTranscriber instance for consistent embeddings
            
        Returns:
            List of search results with metadata
        """
        try:
            # Use Gemini embeddings if transcriber is provided (for consistency)
            if transcriber:
                query_embedding = transcriber.get_embedding(query)
                if query_embedding:
                    results = self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=limit,
                        include=['documents', 'metadatas', 'distances']
                    )
                else:
                    # Fallback to text query if embedding fails
                    results = self.collection.query(
                        query_texts=[query],
                        n_results=limit,
                        include=['documents', 'metadatas', 'distances']
                    )
            else:
                # Use ChromaDB's default text embedding
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit,
                    include=['documents', 'metadatas', 'distances']
                )
            
            search_results = []
            
            if results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    # Calculate similarity score (ChromaDB returns distances)
                    distance = results['distances'][0][i] if results['distances'] else 0
                    similarity = 1.0 - distance  # Convert distance to similarity
                    
                    if similarity >= threshold:
                        result = {
                            'id': doc_id,
                            'content': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'similarity': similarity,
                            'distance': distance
                        }
                        search_results.append(result)
                        
            return search_results
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
            
    def voice_search(self, audio_query_path: Path, transcriber) -> List[Dict[str, Any]]:
        """Transcribe audio query and perform semantic search.
        
        Args:
            audio_query_path: Path to audio file with search query
            transcriber: Transcriber instance for audio-to-text conversion
            
        Returns:
            List of search results
        """
        try:
            # Transcribe the audio query
            query_text = transcriber.transcribe_audio(audio_query_path)
            if not query_text:
                print("Failed to transcribe audio query")
                return []
                
            print(f"Voice query: {query_text}")
            
            # Perform text search with transcribed query
            return self.search_similar(query_text)
            
        except Exception as e:
            print(f"Voice search error: {e}")
            return []
            
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            
            # Get sample of documents to analyze
            sample_size = min(100, count)
            if count > 0:
                sample = self.collection.get(limit=sample_size, include=['metadatas'])
                
                # Count unique files
                unique_files = set()
                total_chunks = 0
                
                for metadata in sample['metadatas']:
                    unique_files.add(metadata.get('source_file', ''))
                    total_chunks += 1
                    
                return {
                    'total_chunks': count,
                    'unique_files': len(unique_files),
                    'sample_size': sample_size,
                    'avg_chunks_per_file': count / len(unique_files) if unique_files else 0
                }
            else:
                return {
                    'total_chunks': 0,
                    'unique_files': 0,
                    'sample_size': 0,
                    'avg_chunks_per_file': 0
                }
                
        except Exception as e:
            print(f"Stats error: {e}")
            return {'error': str(e)}
            
    def remove_transcript(self, transcript_path: Path) -> bool:
        """Remove a transcript from the vector store.
        
        Args:
            transcript_path: Path to the transcript file to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_id = str(transcript_path.absolute())
            
            # Find all chunks for this file
            results = self.collection.get(
                where={"source_file": {"$eq": str(transcript_path)}}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                print(f"Removed transcript: {transcript_path.name} ({len(results['ids'])} chunks)")
                return True
            else:
                print(f"Transcript not found in vector store: {transcript_path.name}")
                return False
                
        except Exception as e:
            print(f"Error removing transcript {transcript_path}: {e}")
            return False
            
    def rebuild_index(self, transcripts_dir: Path, transcriber=None) -> bool:
        """Rebuild the entire vector store from transcript files.
        
        Args:
            transcripts_dir: Directory containing transcript files
            transcriber: Optional transcriber for generating embeddings
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear existing collection
            self.client.delete_collection("transcripts")
            self.collection = self.client.create_collection(
                name="transcripts",
                metadata={
                    "description": "Voice dictation transcripts with semantic search",
                    "embedding_model": "gemini-text-embedding-004",
                    "embedding_provider": "google-gemini"
                }
            )
            
            # Add all transcript files
            transcript_files = list(transcripts_dir.glob("*.txt")) + list(transcripts_dir.glob("*.md"))
            
            success_count = 0
            for transcript_file in transcript_files:
                if self.add_transcript(transcript_file, transcriber):
                    success_count += 1
                    
            print(f"Rebuilt vector store: {success_count}/{len(transcript_files)} transcripts added")
            return success_count > 0
            
        except Exception as e:
            print(f"Error rebuilding index: {e}")
            return False
            
    def save_search_results(self, query: str, results: List[Dict[str, Any]], output_dir: Path, format: str = 'md') -> Optional[Path]:
        """Save search results to a file.
        
        Args:
            query: The search query
            results: Search results from search_similar()
            output_dir: Directory to save results file
            format: File format ('md' or 'txt')
            
        Returns:
            Path to saved file, or None if failed
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
            filename = f"search_{timestamp}_{query_hash}.{format}"
            output_path = output_dir / filename
            
            if format == 'md':
                # Format results as Markdown
                content = [
                    f"# Search Results",
                    f"",
                    f"**Query:** {query}",
                    f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"**Results:** {len(results)}",
                    f"",
                    f"---",
                    f""
                ]
                
                for i, result in enumerate(results, 1):
                    metadata = result['metadata']
                    similarity = result['similarity']
                    
                    content.extend([
                        f"## Result {i} (Similarity: {similarity:.3f})",
                        f"",
                        f"**Source:** {metadata.get('file_name', 'Unknown')}",
                        f"**Chunk:** {metadata.get('chunk_index', 0) + 1}/{metadata.get('total_chunks', 1)}",
                        f"",
                        f"```",
                        result['content'],
                        f"```",
                        f""
                    ])
            else:
                # Format results as plain text
                content = [
                    f"Search Results",
                    f"=============",
                    f"",
                    f"Query: {query}",
                    f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"Results: {len(results)}",
                    f"",
                    f"---",
                    f""
                ]
                
                for i, result in enumerate(results, 1):
                    metadata = result['metadata']
                    similarity = result['similarity']
                    
                    content.extend([
                        f"Result {i} (Similarity: {similarity:.3f})",
                        f"",
                        f"Source: {metadata.get('file_name', 'Unknown')}",
                        f"Chunk: {metadata.get('chunk_index', 0) + 1}/{metadata.get('total_chunks', 1)}",
                        f"",
                        result['content'],
                        f"",
                        f"---",
                        f""
                    ])
                    
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
                
            return output_path
            
        except Exception as e:
            print(f"Error saving search results: {e}")
            return None
