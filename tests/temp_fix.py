from typing import Dict, Any, Optional, List
import os
import json
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import anthropic

from utils.config import config
from src.vector_store import VectorStore

class ReportGenerator:
    def __init__(self):
        self.anthropic_client = None
        self.api_version = "unknown"

        # Validate the API key format first
        if not config.anthropic_api_key or not config.anthropic_api_key.startswith("sk-ant"):
            print("
WARNING: The Anthropic API key does not have the expected format.")

        try:
            self.anthropic_client = anthropic.Anthropic(api_key=config.anthropic_api_key)
            if hasattr(self.anthropic_client, 'messages'):
                self.api_version = "messages"
            else:
                self.api_version = "completions"
        except (AttributeError, TypeError) as e:
            try:
                self.anthropic_client = anthropic.Client(api_key=config.anthropic_api_key)
                self.api_version = "client"
            except Exception as e:
                print(f"
Error initializing Anthropic client: {e}")
                raise

        print(f"Using Anthropic API version: {self.api_version}")
        self.vector_store = VectorStore()
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(self.data_dir, exist_ok=True)
