"""
Configuration utilities for YouTube Analyzer.
"""
import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables
load_dotenv()

class Config(BaseModel):
    """Configuration settings for the application."""
    # YouTube API
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "")

    # Anthropic API
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")

    # Application settings
    max_videos: int = 10

    def validate_config(self) -> bool:
        """
        Validate that all required configuration values are set.

        Returns:
            bool: True if all required values are set, False otherwise.
        """
        required_keys = ["youtube_api_key", "anthropic_api_key", "supabase_url", "supabase_key"]
        missing_keys = []

        for key in required_keys:
            if not getattr(self, key):
                missing_keys.append(key)

        if missing_keys:
            print(f"Missing required configuration: {', '.join(missing_keys)}")
            return False

        return True

# Create a global config instance
config = Config()
