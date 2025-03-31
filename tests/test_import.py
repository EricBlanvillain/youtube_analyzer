#!/usr/bin/env python3
"""
Test script to check if the WorkflowOrchestrator can be imported properly.
"""

try:
    from src.orchestrator import WorkflowOrchestrator
    print("Successfully imported WorkflowOrchestrator")
except ImportError as e:
    print(f"Error importing WorkflowOrchestrator: {e}")

# Try importing each dependency to check for issues
try:
    import anthropic
    print(f"anthropic version: {anthropic.__version__}")
except ImportError as e:
    print(f"Error importing anthropic: {e}")

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    print("Successfully imported YouTubeTranscriptApi")
except ImportError as e:
    print(f"Error importing YouTubeTranscriptApi: {e}")

try:
    import diskcache
    print("Successfully imported diskcache")
except ImportError as e:
    print(f"Error importing diskcache: {e}")

try:
    from src.data_retriever import DataRetriever
    print("Successfully imported DataRetriever")
except ImportError as e:
    print(f"Error importing DataRetriever: {e}")

try:
    from src.report_generator import ReportGenerator
    print("Successfully imported ReportGenerator")
except ImportError as e:
    print(f"Error importing ReportGenerator: {e}")

try:
    from src.vector_store import VectorStore
    print("Successfully imported VectorStore")
except ImportError as e:
    print(f"Error importing VectorStore: {e}")

try:
    from utils.config import config
    print("Successfully imported config")
except ImportError as e:
    print(f"Error importing config: {e}")
