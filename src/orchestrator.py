"""
Workflow orchestrator for YouTube Analyzer.
This module coordinates the overall process of retrieving,
analyzing, and answering questions about YouTube videos.
"""
from typing import List, Dict, Any, Optional, Tuple
import os
import json
from datetime import datetime

from src.data_retriever import DataRetriever
from src.report_generator import ReportGenerator
from src.qa_agent import QAAgent
from utils.config import config

class WorkflowOrchestrator:
    """Orchestrator for the YouTube analysis workflow."""

    def __init__(self):
        """Initialize the orchestrator with all required agents."""
        self.data_retriever = DataRetriever()
        self.report_generator = ReportGenerator()
        self.qa_agent = QAAgent()
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(self.data_dir, exist_ok=True)

        # Session data
        self.current_channel = None
        self.current_videos = []
        self.analyzed_videos = []

    def start_workflow(self):
        """Start the main workflow process."""
        print("\n" + "="*50)
        print("Welcome to YouTube Analyzer")
        print("="*50 + "\n")

        # Validate configuration
        if not config.validate_config():
            print("Please set up your environment variables and try again.")
            return

        # Get channel
        channel_name = input("Enter the YouTube channel name you want to analyze: ")
        return self.analyze_channel(channel_name)

    def analyze_channel(self, channel_name: str) -> bool:
        """
        Analyze a YouTube channel.

        Args:
            channel_name: Name of the YouTube channel.

        Returns:
            True if successful, False otherwise.
        """
        print(f"\nRetrieving information for channel: {channel_name}")
        channel_info, videos = self.data_retriever.get_channel_and_videos(channel_name)

        if not channel_info:
            print(f"Could not retrieve information for channel: {channel_name}")
            return False

        if not videos:
            print(f"No suitable videos found for channel: {channel_info['title']}")
            return False

        # Save channel and videos
        self.current_channel = channel_info
        self.current_videos = videos

        # Display channel info
        print("\n" + "-"*50)
        print(f"Channel: {channel_info['title']}")
        print(f"Subscribers: {channel_info['subscriber_count']}")
        print(f"Total views: {channel_info['view_count']}")
        print(f"Total videos: {channel_info['video_count']}")
        print("-"*50 + "\n")

        # Display videos
        self.display_videos()

        # Ask user to select videos
        selected_videos = self.select_videos()

        if not selected_videos:
            print("No videos selected for analysis.")
            return False

        # Analyze selected videos
        return self.analyze_videos(selected_videos)

    def display_videos(self):
        """Display the list of videos."""
        print(f"Found {len(self.current_videos)} recent long videos:")
        print("-"*50)

        for i, video in enumerate(self.current_videos, 1):
            # Format duration in a human-readable format
            duration_mins = video["duration_seconds"] // 60
            duration_secs = video["duration_seconds"] % 60
            duration_str = f"{duration_mins}:{duration_secs:02d}"

            print(f"{i}. {video['title']}")
            print(f"   Duration: {duration_str} | Views: {video['view_count']}")

        print("-"*50)

    def select_videos(self) -> List[Dict[str, Any]]:
        """
        Let the user select videos for analysis.

        Returns:
            List of selected video information dictionaries.
        """
        try:
            # Get user input
            selection_input = input("\nEnter the numbers of videos to analyze (comma-separated, e.g., 1,3,5): ")

            # Parse input
            selection = []
            for part in selection_input.split(","):
                part = part.strip()
                if "-" in part:
                    # Handle ranges (e.g., 1-3)
                    start, end = map(int, part.split("-"))
                    selection.extend(range(start, end + 1))
                else:
                    # Handle individual numbers
                    selection.append(int(part))

            # Validate selection
            valid_selection = []
            for idx in selection:
                if 1 <= idx <= len(self.current_videos):
                    valid_selection.append(idx)
                else:
                    print(f"Ignoring invalid selection: {idx}")

            # Return selected videos
            return [self.current_videos[idx - 1] for idx in valid_selection]
        except Exception as e:
            print(f"Error parsing selection: {e}")
            return []

    def analyze_videos(self, videos: List[Dict[str, Any]]) -> bool:
        """
        Analyze the selected videos.

        Args:
            videos: List of video information dictionaries.

        Returns:
            True if at least one video was successfully analyzed, False otherwise.
        """
        successful_analyses = 0

        for video in videos:
            print(f"\nProcessing video: {video['title']}")
            report = self.report_generator.generate_report(video)

            if report:
                print(f"Analysis completed for '{video['title']}'")
                self.analyzed_videos.append(report)
                successful_analyses += 1
            else:
                print(f"Failed to analyze '{video['title']}'")

        if successful_analyses > 0:
            print(f"\nSuccessfully analyzed {successful_analyses} out of {len(videos)} videos.")
            self.save_session()
            return True
        else:
            print("\nFailed to analyze any videos.")
            return False

    def save_session(self):
        """Save the current session data."""
        session_data = {
            "timestamp": datetime.now().isoformat(),
            "channel": self.current_channel,
            "analyzed_video_ids": [video["video_id"] for video in self.analyzed_videos]
        }

        session_file = os.path.join(self.data_dir, "session.json")
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)

        print(f"Session data saved to {session_file}")

    def load_session(self) -> bool:
        """
        Load a previous session.

        Returns:
            True if session loaded successfully, False otherwise.
        """
        session_file = os.path.join(self.data_dir, "session.json")

        if not os.path.exists(session_file):
            print("No previous session found.")
            return False

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            self.current_channel = session_data["channel"]

            # Load analyzed videos reports
            for video_id in session_data["analyzed_video_ids"]:
                report = self.qa_agent.get_report_by_id(video_id)
                if report:
                    self.analyzed_videos.append(report)

            print(f"Loaded session from {session_data['timestamp']}")
            print(f"Channel: {self.current_channel['title']}")
            print(f"Analyzed videos: {len(self.analyzed_videos)}")

            return True
        except Exception as e:
            print(f"Error loading session: {e}")
            return False

    def ask_question(self, question: str, specific_videos: Optional[List[str]] = None) -> str:
        """
        Ask a question about analyzed videos.

        Args:
            question: The question to answer.
            specific_videos: Optional list of specific video IDs to consider.

        Returns:
            Answer to the question.
        """
        if not self.analyzed_videos and not self.load_session():
            return "No analyzed videos available. Please analyze some videos first."

        video_ids = specific_videos
        if not video_ids:
            # Use all analyzed videos
            video_ids = [video["video_id"] for video in self.analyzed_videos]

        return self.qa_agent.answer_question(question, video_ids)

    def interactive_qa(self):
        """Start an interactive Q&A session."""
        if not self.analyzed_videos and not self.load_session():
            print("No analyzed videos available. Please analyze some videos first.")
            return

        print("\n" + "="*50)
        print("Q&A Session - Ask questions about the analyzed videos")
        print("(Type 'exit' to end the session)")
        print("="*50)

        # List available videos
        videos = self.qa_agent.list_available_reports()
        print("\nAvailable videos:")
        for i, video in enumerate(videos, 1):
            print(f"{i}. {video['video_title']}")

        while True:
            question = input("\nYour question (or 'exit'): ")
            if question.lower() == "exit":
                break

            answer = self.ask_question(question)
            print(f"\nAnswer: {answer}")

    def run(self):
        """Run the main application loop."""
        while True:
            print("\n" + "="*50)
            print("YouTube Analyzer - Main Menu")
            print("="*50)
            print("1. Analyze a new channel")
            print("2. Load previous session")
            print("3. Ask questions about analyzed videos")
            print("4. Exit")

            choice = input("\nEnter your choice (1-4): ")

            if choice == "1":
                self.start_workflow()
            elif choice == "2":
                if self.load_session():
                    print("Session loaded successfully.")
                else:
                    print("Failed to load session.")
            elif choice == "3":
                self.interactive_qa()
            elif choice == "4":
                print("Thank you for using YouTube Analyzer!")
                break
            else:
                print("Invalid choice. Please try again.")
