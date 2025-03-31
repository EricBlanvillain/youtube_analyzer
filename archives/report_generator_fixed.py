"""
Report generator for YouTube Analyzer.
This module handles downloading video transcripts and sending them
to the Anthropic API for analysis.
"""
from typing import Dict, Any, Optional, List
import os
import json
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import anthropic

from utils.config import config
from src.vector_store import VectorStore

class ReportGenerator:
    """Agent for generating analysis reports from video transcripts."""

    def __init__(self):
        """Initialize the report generator with Anthropic client and vector store."""
        # Try to handle different versions of the Anthropic API
        self.anthropic_client = None
        self.api_version = "unknown"

        # Validate the API key format first
        if not config.anthropic_api_key or not config.anthropic_api_key.startswith("sk-ant"):
            print("\nWARNING: The Anthropic API key does not have the expected format. It should start with 'sk-ant'.")
            print("Please check your .env file and ensure you have a valid API key from Anthropic Console.")
            print("Current API key format:", config.anthropic_api_key[:10] + "..." if config.anthropic_api_key else "None")

        # Try each version of the API in sequence
        try:
            # First try newest version with messages API
            self.anthropic_client = anthropic.Anthropic(api_key=config.anthropic_api_key)
            # Test if messages attribute exists
            if hasattr(self.anthropic_client, 'messages'):
                self.api_version = "messages"
            else:
                # It's newer version but with completions API
                self.api_version = "completions"
        except (AttributeError, TypeError) as e:
            print(f"\nError initializing newer Anthropic client: {e}")
            # Fall back to older version (Client)
            try:
                self.anthropic_client = anthropic.Client(api_key=config.anthropic_api_key)
                self.api_version = "client"
            except Exception as e:
                print(f"\nError initializing Anthropic client: {e}")
                print("\nPossible causes:")
                print("1. Your API key may be expired or invalid")
                print("2. You may not have the anthropic library installed")
                print("3. There could be network connectivity issues")
                print("\nTroubleshooting steps:")
                print("1. Check your API key in the .env file")
                print("2. Ensure you've run 'pip install anthropic==0.3.11'")
                print("3. Try visiting https://console.anthropic.com/ to verify your API key")
                raise

        print(f"Using Anthropic API version: {self.api_version}")

        # Initialize vector store
        self.vector_store = VectorStore()

        # Set data directory
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(self.data_dir, exist_ok=True)

    def get_transcript(self, video_id: str) -> Optional[str]:
        """
        Get transcript for a YouTube video.

        Args:
            video_id: YouTube video ID.

        Returns:
            Transcript text or None if unavailable.
        """
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([entry["text"] for entry in transcript_list])

            # Save transcript to file
            transcript_file = os.path.join(self.data_dir, f"{video_id}_transcript.txt")
            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(transcript_text)

            return transcript_text
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            print(f"Transcript not available for video {video_id}: {e}")
            return None
        except Exception as e:
            print(f"Error retrieving transcript for video {video_id}: {e}")
            return None

    def analyze_transcript(self, video_info: Dict[str, Any], transcript: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a video transcript using Anthropic API.

        Args:
            video_info: Information about the video.
            transcript: Video transcript text.

        Returns:
            Analysis report or None if analysis failed.
        """
        try:
            # Prepare prompt for Claude
            prompt = f"""
            You are Claude, an expert AI assistant specialized in analyzing YouTube content. Your expertise includes content analysis, topic identification, knowledge extraction, and audience engagement assessment.

            TASK CONTEXT:
            You're analyzing a YouTube video transcript for a tool that helps users understand video content without watching it. The analysis will be used to generate reports and answer user questions about SPECIFIC details mentioned in the video.

            VIDEO INFORMATION:
            Title: "{video_info['title']}"
            Video ID: {video_info['id']}

            ANALYSIS TASKS:
            1. Identify the 3-7 main topics and subtopics discussed in the video
            2. Extract 5-10 key takeaways or essential points (clear, concise bullet points)
            3. Identify at least 15 important facts, statistics, quotes, and references mentioned - be as specific and detailed as possible
            4. Identify any technical details, methods, products, or tools mentioned specifically by name
            5. Extract timestamps or approximate locations in the transcript for important segments (beginning, middle, end)
            6. Note any examples, case studies, or stories used to illustrate points
            7. Assess the presenter's tone, style, and presentation approach
            8. Determine the target audience and content purpose
            9. Evaluate the educational/informational value of the content

            FORMAT REQUIREMENTS:
            Return your analysis as a structured JSON with these keys:
            - main_topics: [List of main topics covered]
            - key_points: [List of the most important takeaways as concise bullet points]
            - important_facts: [List of specific factual statements, statistics, quotes with attributions when available]
            - technical_details: [List of any technical methods, products, tools or resources mentioned]
            - examples_and_stories: [List of examples, case studies, or stories mentioned]
            - important_segments: [List of important segments with approximate location (beginning, middle, end) and brief description]
            - tone_and_style: Brief assessment of communication style, presentation approach, and delivery
            - target_audience: Who this content appears to be created for
            - content_quality: Brief assessment of educational/informational value
            - overall_summary: A clear, concise 2-3 sentence summary capturing the video's essence
            - detailed_summary: A more comprehensive summary (5-7 sentences) including key arguments and insights

            IMPORTANT GUIDANCE:
            - Focus on extracting SPECIFIC details that would be helpful for answering detailed questions later
            - Include exact numbers, names, and specific references mentioned
            - When technical terms or names are mentioned, extract them precisely
            - Be objective and focus on identifying information rather than evaluating its accuracy
            - When uncertain about a topic, make a reasonable inference based on context
            - Ensure your response is properly formatted as valid JSON
            - Do not include any preliminary text before the JSON begins

            TRANSCRIPT:
            {transcript[:100000]}  # Truncate if too long
            """

            # Call Anthropic API using the appropriate method based on version
            response_text = ""
            try:
                if self.api_version == "messages":
                    # Newest API with messages.create
                    response = self.anthropic_client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=8000,
                        temperature=0.0,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    response_text = response.content[0].text
                elif self.api_version == "completions":
                    # Newer API with completions
                    response = self.anthropic_client.completions.create(
                        model="claude-2.0",
                        prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
                        max_tokens_to_sample=8000,
                        temperature=0,
                    )
                    response_text = response.completion
                else:
                    # Old API (Client class with completion)
                    response = self.anthropic_client.completion(
                        prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
                        model="claude-2.0",
                        max_tokens_to_sample=8000,
                        temperature=0.0,
                    )
                    response_text = response.completion
            except Exception as api_error:
                print(f"Error calling Anthropic API: {api_error}")
                if "401" in str(api_error) or "authentication" in str(api_error).lower():
                    print("\nAuthentication error with the Anthropic API.")
                    print("Please check your API key in the .env file and ensure it is valid.")
                    print("You can get a new API key from https://console.anthropic.com/")
                    print("Remember that API keys may expire or be revoked.")
                raise

            # Extract JSON from response
            try:
                # Try to find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1

                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    analysis = json.loads(json_str)
                else:
                    # Structured format if JSON parsing fails
                    analysis = {
                        "main_topics": ["Unable to parse main topics"],
                        "key_points": ["Unable to parse key points"],
                        "important_facts": ["Unable to parse important facts"],
                        "technical_details": ["Unable to parse technical details"],
                        "examples_and_stories": ["Unable to parse examples"],
                        "important_segments": ["Unable to parse important segments"],
                        "tone_and_style": "Unable to determine",
                        "overall_summary": response_text[:500]  # Use part of response as summary
                    }
            except json.JSONDecodeError:
                # Try to find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1

                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    analysis = json.loads(json_str)
                else:
                    # Structured format if JSON parsing fails
                    analysis = {
                        "main_topics": ["Unable to parse main topics"],
                        "key_points": ["Unable to parse key points"],
                        "important_facts": ["Unable to parse important facts"],
                        "technical_details": ["Unable to parse technical details"],
                        "examples_and_stories": ["Unable to parse examples"],
                        "important_segments": ["Unable to parse important segments"],
                        "tone_and_style": "Unable to determine",
                        "target_audience": "General audience",
                        "content_quality": "Unable to assess",
                        "overall_summary": response_text[:500],  # Use part of response as summary
                        "detailed_summary": response_text[:1000]  # Use longer part for detailed summary
                    }

            # Ensure all expected fields are present with defaults if missing
            required_fields = {
                "main_topics": ["No specific topics identified"],
                "key_points": ["No key points extracted"],
                "important_facts": ["No important facts identified"],
                "technical_details": ["No technical details mentioned"],
                "examples_and_stories": ["No examples or stories mentioned"],
                "important_segments": ["No important segments identified"],
                "tone_and_style": "Not analyzed",
                "target_audience": "General audience",
                "content_quality": "Not evaluated",
                "overall_summary": "No summary available",
                "detailed_summary": "No detailed summary available"
            }

            for field, default in required_fields.items():
                if field not in analysis:
                    analysis[field] = default

            # Create the full report
            report = {
                "video_id": video_info["id"],
                "video_title": video_info["title"],
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis": analysis
            }

            # Save report to file
            report_file = os.path.join(self.data_dir, f"{video_info['id']}_report.json")
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

            return report
        except Exception as e:
            print(f"Error analyzing transcript: {e}")
            return None

    def generate_report(self, video_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate analysis report for a video.

        Args:
            video_info: Information about the video.

        Returns:
            Report data or None if generation failed.
        """
        video_id = video_info["id"]
        print(f"\nGenerating report for video: {video_info['title']} (ID: {video_id})")

        # Check if report already exists
        report_file = os.path.join(self.data_dir, f"{video_id}_report.json")
        if os.path.exists(report_file):
            print(f"Report already exists for video {video_id}. Loading existing report...")
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    report = json.load(f)

                # Index existing report in vector store if needed
                self._index_report_in_vector_store(report)

                return report
            except Exception as e:
                print(f"Error loading existing report: {e}")
                print("Generating new report...")

        # Get video transcript
        transcript = self.get_transcript(video_id)
        if not transcript:
            print(f"Could not retrieve transcript for video {video_id}")
            return None

        # Analyze transcript
        analysis = self.analyze_transcript(video_info, transcript)
        if not analysis:
            print(f"Analysis failed for video {video_id}")
            return None

        # Create report
        report = {
            "video_id": video_id,
            "video_title": video_info["title"],
            "channel_title": video_info["channel_title"] if "channel_title" in video_info else "Unknown",
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis": analysis
        }

        # Save report to file
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            print(f"Report saved successfully for video {video_id}")

            # Index report and transcript in vector store
            self._index_report_in_vector_store(report)
            self._index_transcript_in_vector_store(video_id, video_info['title'], transcript)

            return report
        except Exception as e:
            print(f"Error saving report for video {video_id}: {e}")
            return report  # Still return the report even if saving failed

    def _index_report_in_vector_store(self, report: Dict[str, Any]) -> None:
        """
        Index a report in the vector store.

        Args:
            report: Report data dictionary.
        """
        try:
            print(f"Indexing report for video {report['video_id']} in vector store...")
            self.vector_store.index_report(report)
            print("Report indexed successfully.")
        except Exception as e:
            print(f"Error indexing report in vector store: {e}")

    def _index_transcript_in_vector_store(self, video_id: str, video_title: str, transcript_text: str) -> None:
        """
        Index a transcript in the vector store.

        Args:
            video_id: YouTube video ID.
            video_title: Video title.
            transcript_text: Transcript text.
        """
        try:
            print(f"Indexing transcript for video {video_id} in vector store...")
            self.vector_store.index_transcript(video_id, video_title, transcript_text)
            print("Transcript indexed successfully.")
        except Exception as e:
            print(f"Error indexing transcript in vector store: {e}")
