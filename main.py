#usr/bin/env python3
"""
YouTube Analyzer - Main application script.
This script is the entry point for the YouTube Analyzer application.
"""
import sys
import os

from src.orchestrator import WorkflowOrchestrator
from src.vector_store import VectorStore
from utils.config import config

def reindex_all_data():
    """Reindex all data in the vector store."""
    print("\nReindexing all data in the vector store...")
    try:
        vector_store = VectorStore()
        vector_store.reindex_all_data()
        print("\nAll data has been successfully reindexed!")
        print("The vector store is now optimized for better query results.")
    except Exception as e:
        print(f"\nError reindexing data: {e}")
        return 1
    return 0

def main():
    """Main entry point for the application."""
    print("Initializing YouTube Analyzer...")

    # Check if any command line arguments were provided
    if len(sys.argv) > 1:
        if sys.argv[1] == "--reindex":
            return reindex_all_data()

    # Check environment variables
    if not config.validate_config():
        print("\nMissing required environment variables. Please check your .env file.")
        print("Required variables:")
        print("- YOUTUBE_API_KEY: For accessing the YouTube API")
        print("- ANTHROPIC_API_KEY: For accessing the Anthropic API")
        print("- SUPABASE_URL: Your Supabase project URL")
        print("- SUPABASE_KEY: Your Supabase API key")

        # Create example .env file if it doesn't exist
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if not os.path.exists(env_file):
            try:
                with open(env_file, "w", encoding="utf-8") as f:
                    f.write("# YouTube API credentials\n")
                    f.write("YOUTUBE_API_KEY=your_youtube_api_key\n\n")
                    f.write("# Anthropic API credentials\n")
                    f.write("ANTHROPIC_API_KEY=your_anthropic_api_key\n\n")
                    f.write("# Supabase credentials\n")
                    f.write("SUPABASE_URL=your_supabase_url\n")
                    f.write("SUPABASE_KEY=your_supabase_key\n")
                print(f"\nCreated example .env file at: {env_file}")
                print("Please fill in your API keys and restart the application.")
            except Exception as e:
                print(f"Error creating example .env file: {e}")

        return 1

    # Show usage information
    print("\nUsage:")
    print("  Run with no arguments to start the main application")
    print("  Run with --reindex to rebuild the vector database")

    # Start the orchestrator
    try:
        orchestrator = WorkflowOrchestrator()
        orchestrator.run()
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
        return 0
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
