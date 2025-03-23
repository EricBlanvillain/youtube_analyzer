"""
Vector store for YouTube Analyzer.
This module handles chunking, embedding, and retrieval of reports and transcripts
using ChromaDB/FAISS for efficient semantic search.
"""
from typing import List, Dict, Any, Optional, Tuple, Union
import os
import json
import time
import hashlib
import threading
from pathlib import Path
import diskcache

import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

class VectorStore:
    """
    Vector database for storing and retrieving YouTube video analysis reports and transcripts.
    Uses ChromaDB with FAISS backend for efficient vector similarity search.
    Implements chunking and caching for improved performance.
    """

    def __init__(self):
        """Initialize the vector store with ChromaDB client and embedding function."""
        # Set up paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        self.vector_dir = os.path.join(self.data_dir, "vector_db")
        self.cache_dir = os.path.join(self.data_dir, "cache")

        # Create directories if they don't exist
        os.makedirs(self.vector_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

        # Initialize disk cache for embeddings
        self.cache = diskcache.Cache(self.cache_dir)

        # Initialize text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
        )

        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(path=self.vector_dir)

        # Use Sentence Transformers for embeddings
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
            device="cpu"
        )

        # Initialize or get collections
        self.reports_collection = self._get_or_create_collection("reports")
        self.transcripts_collection = self._get_or_create_collection("transcripts")

        # Lock for thread safety
        self.lock = threading.Lock()

    def _get_or_create_collection(self, name: str) -> chromadb.Collection:
        """
        Get an existing collection or create a new one.

        Args:
            name: Name of the collection.

        Returns:
            ChromaDB collection.
        """
        try:
            return self.client.get_collection(name=name, embedding_function=self.embedding_function)
        except ValueError:
            return self.client.create_collection(name=name, embedding_function=self.embedding_function)

    def _generate_chunk_id(self, video_id: str, index: int, total: int) -> str:
        """
        Generate a unique ID for a chunk.

        Args:
            video_id: YouTube video ID.
            index: Chunk index.
            total: Total number of chunks.

        Returns:
            Unique chunk ID.
        """
        return f"{video_id}_chunk_{index}_of_{total}"

    def _get_cache_key(self, text: str) -> str:
        """
        Generate a cache key for a text chunk.

        Args:
            text: Text to generate key for.

        Returns:
            Cache key as string.
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def index_report(self, report: Dict[str, Any]) -> None:
        """
        Index a report in the vector database.

        Args:
            report: Report data dictionary.
        """
        video_id = report["video_id"]

        # Remove existing chunks for this video if any
        with self.lock:
            try:
                # Get existing chunks for this video
                existing_chunks = self.reports_collection.get(
                    where={"video_id": video_id}
                )

                # Delete if any exist
                if existing_chunks and existing_chunks['ids']:
                    self.reports_collection.delete(
                        ids=existing_chunks['ids']
                    )
            except Exception as e:
                print(f"Warning: Could not delete existing report chunks for {video_id}: {e}")

        # Prepare report sections for chunking
        sections = []

        # Add main metadata
        sections.append(f"Video title: {report['video_title']}")
        if 'channel_title' in report:
            sections.append(f"Channel: {report['channel_title']}")

        # Add analysis sections
        if 'analysis' in report:
            analysis = report['analysis']

            # Main topics
            if 'main_topics' in analysis:
                sections.append(f"Main topics: {', '.join(analysis['main_topics'])}")

            # Key points
            if 'key_points' in analysis:
                points_text = "Key points:\n" + "\n".join([f"- {point}" for point in analysis['key_points']])
                sections.append(points_text)

            # Important facts
            if 'important_facts' in analysis:
                facts_text = "Important facts:\n" + "\n".join([f"- {fact}" for fact in analysis['important_facts']])
                sections.append(facts_text)

            # Technical details
            if 'technical_details' in analysis and analysis['technical_details']:
                tech_text = "Technical details:\n" + "\n".join([f"- {detail}" for detail in analysis['technical_details']])
                sections.append(tech_text)

            # Examples and stories
            if 'examples_and_stories' in analysis and analysis['examples_and_stories']:
                examples_text = "Examples and stories:\n" + "\n".join([f"- {example}" for example in analysis['examples_and_stories']])
                sections.append(examples_text)

            # Important segments
            if 'important_segments' in analysis and analysis['important_segments']:
                segments_text = "Important segments:\n" + "\n".join([f"- {segment}" for segment in analysis['important_segments']])
                sections.append(segments_text)

            # Summaries
            if 'detailed_summary' in analysis:
                sections.append(f"Detailed summary: {analysis['detailed_summary']}")
            if 'overall_summary' in analysis:
                sections.append(f"Overall summary: {analysis['overall_summary']}")

        # Combine sections and split into chunks
        combined_text = "\n\n".join(sections)
        chunks = self.text_splitter.split_text(combined_text)

        # Add chunks to vector store
        ids = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = self._generate_chunk_id(video_id, i, len(chunks))
            ids.append(chunk_id)

            metadatas.append({
                "video_id": video_id,
                "video_title": report["video_title"],
                "chunk_index": i,
                "total_chunks": len(chunks),
                "type": "report"
            })

        # Add to collection
        with self.lock:
            self.reports_collection.add(
                documents=chunks,
                ids=ids,
                metadatas=metadatas
            )

        print(f"Indexed report for video {video_id} in {len(chunks)} chunks")

    def index_transcript(self, video_id: str, video_title: str, transcript_text: str) -> None:
        """
        Index a transcript in the vector database.

        Args:
            video_id: YouTube video ID.
            video_title: Title of the video.
            transcript_text: Full transcript text.
        """
        # Remove existing chunks for this video if any
        with self.lock:
            try:
                # Get existing chunks for this video
                existing_chunks = self.transcripts_collection.get(
                    where={"video_id": video_id}
                )

                # Delete if any exist
                if existing_chunks and existing_chunks['ids']:
                    self.transcripts_collection.delete(
                        ids=existing_chunks['ids']
                    )
            except Exception as e:
                print(f"Warning: Could not delete existing transcript chunks for {video_id}: {e}")

        # Split transcript into chunks
        chunks = self.text_splitter.split_text(transcript_text)

        # Add chunks to vector store
        ids = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = self._generate_chunk_id(video_id, i, len(chunks))
            ids.append(chunk_id)

            metadatas.append({
                "video_id": video_id,
                "video_title": video_title,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "type": "transcript"
            })

        # Add to collection
        with self.lock:
            self.transcripts_collection.add(
                documents=chunks,
                ids=ids,
                metadatas=metadatas
            )

        print(f"Indexed transcript for video {video_id} in {len(chunks)} chunks")

    def retrieve_relevant_chunks(
        self,
        query: str,
        n_results: int = 10,
        include_reports: bool = True,
        include_transcripts: bool = True,
        video_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant chunks for a query.

        Args:
            query: User query.
            n_results: Number of results to retrieve.
            include_reports: Whether to include report chunks.
            include_transcripts: Whether to include transcript chunks.
            video_ids: Optional list of video IDs to filter by.

        Returns:
            List of relevant chunks with metadata.
        """
        results = []

        # Query multiple collections as needed
        if include_reports:
            where_clause = {}
            if video_ids:
                where_clause = {"video_id": {"$in": video_ids}}

            with self.lock:
                report_results = self.reports_collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_clause if where_clause else None
                )

            # Process results
            if report_results and len(report_results['documents']) > 0:
                for i, doc in enumerate(report_results['documents'][0]):
                    metadata = report_results['metadatas'][0][i]
                    distance = report_results['distances'][0][i] if 'distances' in report_results else None

                    results.append({
                        "chunk": doc,
                        "metadata": metadata,
                        "distance": distance,
                        "source": "report"
                    })

        if include_transcripts:
            where_clause = {}
            if video_ids:
                where_clause = {"video_id": {"$in": video_ids}}

            with self.lock:
                transcript_results = self.transcripts_collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_clause if where_clause else None
                )

            # Process results
            if transcript_results and len(transcript_results['documents']) > 0:
                for i, doc in enumerate(transcript_results['documents'][0]):
                    metadata = transcript_results['metadatas'][0][i]
                    distance = transcript_results['distances'][0][i] if 'distances' in transcript_results else None

                    results.append({
                        "chunk": doc,
                        "metadata": metadata,
                        "distance": distance,
                        "source": "transcript"
                    })

        # Sort by relevance (distance)
        if results and 'distance' in results[0]:
            results.sort(key=lambda x: x['distance'])

        return results

    def get_context_for_query(self, query: str, video_ids: Optional[List[str]] = None) -> str:
        """
        Get a formatted context string for a query using vector search.

        Args:
            query: User query.
            video_ids: Optional list of video IDs to filter by.

        Returns:
            Formatted context string.
        """
        # Get relevant chunks
        chunks = self.retrieve_relevant_chunks(
            query=query,
            n_results=15,  # Get more chunks for better context
            include_reports=True,
            include_transcripts=True,
            video_ids=video_ids
        )

        if not chunks:
            return "No relevant information found."

        # Organize chunks by video and type
        organized_chunks = {}

        for chunk in chunks:
            video_id = chunk['metadata']['video_id']
            video_title = chunk['metadata']['video_title']
            chunk_type = chunk['source']  # report or transcript

            if video_id not in organized_chunks:
                organized_chunks[video_id] = {
                    'title': video_title,
                    'reports': [],
                    'transcripts': []
                }

            if chunk_type == 'report':
                organized_chunks[video_id]['reports'].append(chunk['chunk'])
            else:
                organized_chunks[video_id]['transcripts'].append(chunk['chunk'])

        # Format context
        context = "Information from analyzed videos:\n\n"

        for video_id, data in organized_chunks.items():
            context += f"Video: {data['title']} (ID: {video_id})\n"

            # Add report information
            if data['reports']:
                context += "\nReport analysis:\n"
                for i, report_chunk in enumerate(data['reports']):
                    context += f"{report_chunk}\n"

            # Add transcript excerpts
            if data['transcripts']:
                context += "\nTranscript excerpts:\n"
                for i, transcript_chunk in enumerate(data['transcripts']):
                    context += f"Excerpt {i+1}: {transcript_chunk}\n"

            context += "\n" + "-"*50 + "\n"

        return context

    def reindex_all_data(self) -> None:
        """
        Reindex all reports and transcripts in the data directory.
        Useful for rebuilding the vector database from scratch.
        """
        print("Reindexing all data...")

        # Clear collections - using get() to get all IDs first, then delete them to avoid the error
        with self.lock:
            try:
                # For reports collection
                reports_to_delete = self.reports_collection.get()
                if reports_to_delete and reports_to_delete['ids']:
                    self.reports_collection.delete(ids=reports_to_delete['ids'])

                # For transcripts collection
                transcripts_to_delete = self.transcripts_collection.get()
                if transcripts_to_delete and transcripts_to_delete['ids']:
                    self.transcripts_collection.delete(ids=transcripts_to_delete['ids'])

                print("Successfully cleared existing collections.")
            except Exception as e:
                print(f"Error clearing collections: {e}")
                # If deletion fails, try recreating the collections
                try:
                    self.client.delete_collection("reports")
                    self.client.delete_collection("transcripts")
                    self.reports_collection = self._get_or_create_collection("reports")
                    self.transcripts_collection = self._get_or_create_collection("transcripts")
                    print("Recreated collections after failed deletion.")
                except Exception as rec_error:
                    print(f"Error recreating collections: {rec_error}")
                    return

        # Find all report files
        for filename in os.listdir(self.data_dir):
            if filename.endswith("_report.json"):
                video_id = filename.replace("_report.json", "")
                report_path = os.path.join(self.data_dir, filename)

                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        report = json.load(f)
                        self.index_report(report)
                except Exception as e:
                    print(f"Error indexing report {filename}: {e}")

                # Check for corresponding transcript
                transcript_path = os.path.join(self.data_dir, f"{video_id}_transcript.txt")
                if os.path.exists(transcript_path):
                    try:
                        with open(transcript_path, "r", encoding="utf-8") as f:
                            transcript_text = f.read()
                            self.index_transcript(
                                video_id=video_id,
                                video_title=report.get("video_title", "Unknown"),
                                transcript_text=transcript_text
                            )
                    except Exception as e:
                        print(f"Error indexing transcript {video_id}: {e}")

        print("Reindexing complete!")

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self.cache.clear()
        print("Cache cleared.")
