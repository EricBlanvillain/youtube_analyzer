"""
Report generator for YouTube Analyzer.
This module handles downloading video transcripts and sending them
to the Anthropic API for analysis.
"""
from typing import Dict, Any, Optional, List, Tuple
import os
import json
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import anthropic
import re
import glob
import time
import ssl
import requests
from requests.adapters import HTTPAdapter

from utils.config import config
from src.vector_store import VectorStore

# Ensure TranscriptsDisabled class is available (sometimes it's not found in the module)
try:
    from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound
except ImportError:
    # Define fallback classes if they can't be imported
    class TranscriptsDisabled(Exception):
        """Exception raised when transcripts are disabled for a video."""
        pass

    class NoTranscriptFound(Exception):
        """Exception raised when no transcript is found for a video."""
        pass

# Create a custom SSL adapter that works with LibreSSL
class TlsAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
        """Create and initialize the urllib3 PoolManager with custom SSL context."""
        ctx = ssl.create_default_context()
        # Set SSL verification mode
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        # Use more lenient options for LibreSSL
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT

        # Use urllib3 PoolManager directly
        import urllib3
        self.poolmanager = urllib3.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx
        )

class ReportGenerator:
    """Agent for generating analysis reports from video transcripts."""

    def __init__(self, data_dir: str = None, data_retriever=None):
        """
        Initialize the ReportGenerator with Claude API access.

        Args:
            data_dir: Directory for storing report data.
            data_retriever: Optional data retriever instance for getting transcripts.
        """
        # Initialize Anthropic client approach
        try:
            # We'll use direct API calls instead of the client library
            self.anthropic_client = None
            self.api_version = "direct"
            print(f"Using Anthropic API version: {self.api_version}")
        except Exception as e:
            print(f"Error initializing Anthropic approach: {e}")
            self.anthropic_client = None
            self.api_version = "direct"  # Will use direct API calls

        # Get the base data directory
        self.data_dir = data_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        os.makedirs(self.data_dir, exist_ok=True)

        # Cache for analyzed videos to avoid re-analyzing the same video multiple times
        self.analyzed_videos_cache = {}

        # Store the data retriever for transcript access
        self.data_retriever = data_retriever

        # Initialize vector store
        try:
            self.vector_store = VectorStore()
        except Exception as e:
            print(f"Error initializing vector store: {e}")
            self.vector_store = None

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

    def analyze_transcript(self, video: Dict[str, Any], transcript: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a video transcript using Claude.

        Args:
            video: The video information.
            transcript: The transcript text.

        Returns:
            Dictionary with the analysis results or None if failed.
        """
        video_id = video["id"]

        # First check if we've already analyzed this video
        if video_id in self.analyzed_videos_cache:
            print(f"Using cached analysis for video: {video['title']}")
            return self.analyzed_videos_cache[video_id]

        # Check if report already exists on disk
        report_file = os.path.join(self.data_dir, f"{video_id}_report.json")
        if os.path.exists(report_file):
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    report = json.load(f)
                print(f"Loaded existing report for video: {video['title']}")
                # Cache the loaded report
                self.analyzed_videos_cache[video_id] = report
                return report
            except Exception as e:
                print(f"Error loading existing report: {e}")
                # Continue with analysis

        print(f"Calling Anthropic API ({self.api_version}) for video: {video_id}")

        # Create the analysis prompt with an improved structure
        prompt = f"""Please analyze this YouTube video transcript and provide insights in JSON format.

Video Title: {video['title']}
Video ID: {video_id}

Transcript:
{transcript[:50000]}  # Truncate to avoid token limits

Analyze the content and extract the following information in a SPECIFIC JSON format:
{{
  "main_topics": [list of 3-5 main topics covered, be specific],
  "key_points": [list of 5-7 most important points or insights, be detailed],
  "technical_details": [list of specific technical details, methods, or concepts mentioned],
  "technologies_mentioned": [list of specific technologies, tools, frameworks, or models mentioned],
  "overall_summary": "A concise 2-3 paragraph summary of the video content that captures the main message and value",
  "important_facts": [list of at least 5 specific facts, statistics, or statements made in the video],
  "examples_and_stories": [list of specific examples, demonstrations, case studies, or stories used to illustrate points],
  "important_segments": [list of key moments or segments with their main points],
  "tone_and_style": "Detailed description of the speaker's presentation style and approach",
  "target_audience": [specific types of audiences who would find this content valuable],
  "content_quality": "Detailed assessment of the depth, accuracy, and practical value of the content"
}}

IMPORTANT GUIDELINES:
1. Be specific and detailed in all fields - avoid generic descriptions
2. Include actual examples and quotes from the video where relevant
3. For important_facts, include specific data points, statistics, or direct quotes
4. For examples_and_stories, describe actual examples used in the video
5. For important_segments, identify specific parts of the video that are particularly valuable
6. Ensure all lists have at least 3-5 detailed items
7. Return ONLY the JSON object, nothing else. Start with '{{' and end with '}}'
"""

        # Call the Anthropic API
        response = self._call_claude_api(prompt)
        if not response:
            print(f"No response received for video: {video['title']}")
            return None

        # Log first part of response for debugging
        print(f"Response received: {len(response)} characters")
        print(f"First 100 chars of response: {response[:100]}")

        # Extract JSON from the response
        try:
            # Try different JSON extraction patterns

            # 1. First try to find JSON blocks with code formatting
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)

            if json_match:
                print(f"Found JSON string in code block from index {json_match.start(1)} to {json_match.end(1)}")
                json_str = json_match.group(1)
                try:
                    analysis = json.loads(json_str)
                    print("Successfully parsed JSON from code block")
                except json.JSONDecodeError as e:
                    print(f"JSON error in code block: {e}, trying to clean JSON string")
                    # Try to clean and fix common JSON issues
                    clean_json = json_str.replace('\n', ' ').replace('\r', '')
                    analysis = json.loads(clean_json)
                    print("Successfully parsed cleaned JSON from code block")
            else:
                # 2. Try to find any JSON-like structure with braces
                json_match = re.search(r'(\{[^{]*"main_topics"[^}]*\})', response, re.DOTALL)
                if json_match:
                    print(f"Found JSON-like structure from index {json_match.start(1)} to {json_match.end(1)}")
                    json_str = json_match.group(1)
                    try:
                        analysis = json.loads(json_str)
                        print("Successfully parsed JSON from extracted structure")
                    except json.JSONDecodeError:
                        print("JSON error in extracted structure, falling back to full response parsing")
                        analysis = json.loads(response)
                        print("Successfully parsed JSON from full response")
                else:
                    # 3. Try direct parsing of the entire response
                    try:
                        analysis = json.loads(response)
                        print("Successfully parsed JSON from full response")
                    except json.JSONDecodeError as full_err:
                        print(f"Failed to parse any JSON from response: {full_err}")
                        # 4. Last resort: try to extract any JSON-like structure
                        start_idx = response.find('{')
                        end_idx = response.rfind('}') + 1
                        if start_idx >= 0 and end_idx > start_idx:
                            json_str = response[start_idx:end_idx]
                            print(f"Attempting to parse JSON from positions {start_idx} to {end_idx}")
                            analysis = json.loads(json_str)
                            print("Successfully parsed JSON from extracted positions")
                        else:
                            raise

            # Ensure we have all the required fields with default values
            analysis = {
                "main_topics": analysis.get("main_topics", []),
                "key_points": analysis.get("key_points", []),
                "technologies_mentioned": analysis.get("technologies_mentioned", []),
                "summary": analysis.get("summary", "No summary available"),
                "relevant_for": analysis.get("relevant_for", ["General audience"])
            }

            # Format the results with a consistent structure
            report = {
                "video_id": video_id,
                "title": video["title"],
                "video_title": video["title"],  # Add video_title as an alias for title
                "analysis_date": datetime.now().isoformat(),
                "analysis_timestamp": datetime.now().isoformat(),  # Add alias for consistency
                "analysis": {
                    "main_topics": analysis.get("main_topics", []),
                    "key_points": analysis.get("key_points", []),
                    "technical_details": analysis.get("technologies_mentioned", []),
                    "technologies_mentioned": analysis.get("technologies_mentioned", []),
                    "overall_summary": analysis.get("summary", ""),
                    "summary": analysis.get("summary", ""),
                    "target_audience": analysis.get("relevant_for", []),
                    "relevant_for": analysis.get("relevant_for", []),
                    "important_facts": analysis.get("important_facts", []),
                    "examples_and_stories": analysis.get("examples_and_stories", []),
                    "examples_and_segments": analysis.get("examples_and_stories", []),  # Alias for consistency
                    "important_segments": analysis.get("important_segments", []),
                    "tone_and_style": analysis.get("tone_and_style", ""),
                    "content_quality": analysis.get("content_quality", "")
                },
                # Also keep top-level fields for backward compatibility
                "main_topics": analysis.get("main_topics", []),
                "key_points": analysis.get("key_points", []),
                "technologies_mentioned": analysis.get("technologies_mentioned", []),
                "summary": analysis.get("summary", ""),
                "relevant_for": analysis.get("relevant_for", []),
                "important_facts": analysis.get("important_facts", []),
                "examples_and_segments": analysis.get("examples_and_stories", [])
            }

            # Save the report to a file
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

            # Add to cache
            self.analyzed_videos_cache[video_id] = report

            # Index in vector store if available
            if self.vector_store:
                try:
                    self._index_report_in_vector_store(report)
                    self._index_transcript_in_vector_store(video_id, video["title"], transcript)
                except Exception as e:
                    print(f"Warning: Error indexing in vector store: {e}")

            return report

        except json.JSONDecodeError as json_err:
            print(f"JSON parsing error for video {video['title']}: {json_err}")
            print(f"Raw response excerpt: {response[:200]}...")

            # Save the raw response for debugging
            error_file = os.path.join(self.data_dir, f"{video_id}_error.txt")
            with open(error_file, "w", encoding="utf-8") as f:
                f.write(response)
            print(f"Full problematic response saved to {error_file}")

            # Create a minimal report with error information
            minimal_report = {
                "video_id": video_id,
                "title": video["title"],
                "analysis_date": datetime.now().isoformat(),
                "main_topics": ["Analysis failed"],
                "key_points": ["JSON parsing error"],
                "technologies_mentioned": [],
                "summary": f"Failed to analyze video due to JSON parsing error: {json_err}",
                "relevant_for": ["N/A"]
            }

            # Cache the minimal report to avoid repeated failing calls
            self.analyzed_videos_cache[video_id] = minimal_report
            return minimal_report

        except Exception as e:
            print(f"Error analyzing transcript for video {video['title']}: {e}")

            # Save the raw response for debugging
            error_file = os.path.join(self.data_dir, f"{video_id}_error.txt")
            with open(error_file, "w", encoding="utf-8") as f:
                f.write(response if response else "No response received")
            print(f"Error details saved to {error_file}")

            # Create a minimal report with error information
            minimal_report = {
                "video_id": video_id,
                "title": video["title"],
                "analysis_date": datetime.now().isoformat(),
                "main_topics": ["Analysis failed"],
                "key_points": [f"Error: {str(e)}"],
                "technologies_mentioned": [],
                "summary": f"Failed to analyze video due to error: {str(e)}",
                "relevant_for": ["N/A"]
            }

            # Cache the minimal report to avoid repeated failing calls
            self.analyzed_videos_cache[video_id] = minimal_report
            return minimal_report

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
        print(f"Getting transcript for video: {video_id}")

        # Use the data_retriever if available, otherwise fall back to local method
        if self.data_retriever:
            transcript = self.data_retriever.get_transcript(video_id)
        else:
            transcript = self.get_transcript(video_id)

        if not transcript:
            print(f"Could not retrieve transcript for video {video_id}")
            return None

        # Analyze transcript
        analysis = self.analyze_transcript(video_info, transcript)
        if not analysis:
            print(f"Analysis failed for video {video_id}")
            return None

        # Create report with consistent structure
        report = {
            "video_id": video_id,
            "video_title": video_info["title"],
            "title": video_info["title"],  # Add alias
            "channel_title": video_info["channel_title"] if "channel_title" in video_info else "Unknown",
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_date": datetime.now().isoformat(),  # Add alias
            "analysis": analysis,
            # Also add flattened fields for backward compatibility
            "main_topics": analysis.get("main_topics", []),
            "key_points": analysis.get("key_points", []),
            "technical_details": analysis.get("technical_details", []),
            "technologies_mentioned": analysis.get("technologies_mentioned", []),
            "summary": analysis.get("summary", analysis.get("overall_summary", "")),
            "relevant_for": analysis.get("relevant_for", []),
            "important_facts": analysis.get("important_facts", []),
            "examples_and_segments": analysis.get("examples_and_stories", [])
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

            # Ensure the report has the required fields in the correct structure
            formatted_report = {
                "video_id": report["video_id"],
                "video_title": report.get("video_title", report.get("title", "Unknown")),  # Handle both field names
                "channel_title": report.get("channel_title", "Unknown"),
                "analysis_timestamp": report.get("analysis_timestamp", datetime.now().isoformat()),
                "main_topics": report.get("main_topics", []) if "main_topics" in report else report.get("analysis", {}).get("main_topics", []),
                "key_points": report.get("key_points", []) if "key_points" in report else report.get("analysis", {}).get("key_points", []),
                "technologies_mentioned": report.get("technologies_mentioned", []) if "technologies_mentioned" in report else report.get("analysis", {}).get("technologies_mentioned", []),
                "summary": report.get("summary", "") if "summary" in report else report.get("analysis", {}).get("summary", ""),
                "relevant_for": report.get("relevant_for", []) if "relevant_for" in report else report.get("analysis", {}).get("relevant_for", ["General audience"])
            }

            self.vector_store.index_report(formatted_report)
            print("Report indexed successfully.")
        except Exception as e:
            print(f"Error indexing report in vector store: {e}")
            raise  # Re-raise the exception to help with debugging

    def _index_transcript_in_vector_store(self, video_id: str, video_title: str, transcript_text: str) -> None:
        """Index transcript in vector store for future queries."""
        try:
            self.vector_store.index_transcript(video_id, video_title, transcript_text)
        except Exception as e:
            print(f"Error indexing transcript in vector store: {e}")

    def generate_digest(self, videos: List[Dict[str, Any]], title: str = None) -> Optional[Dict[str, Any]]:
        """
        Generate a digest of multiple videos using Claude.

        Args:
            videos: List of video information dictionaries.
            title: Optional title for the digest.

        Returns:
            Dictionary with the digest results or None if failed.
        """
        if not videos:
            print("No videos provided for digest generation")
            return None

        # Filter out any videos that don't have report
        valid_videos = []
        failed_videos = []
        skipped_videos = 0
        for video in videos:
            video_id = video["id"]
            report_file = os.path.join(self.data_dir, f"{video_id}_report.json")

            # Check if we've already analyzed this video
            if video_id in self.analyzed_videos_cache:
                valid_videos.append(video)
                continue

            # Check if we have a report saved
            if os.path.exists(report_file):
                try:
                    with open(report_file, "r", encoding="utf-8") as f:
                        report = json.load(f)
                    self.analyzed_videos_cache[video_id] = report
                    valid_videos.append(video)
                    continue
                except Exception as e:
                    print(f"Error loading report for {video['title']}: {e}")

            # Get transcript and analyze
            try:
                print(f"Analyzing video: {video['title']}")
                transcript = self.data_retriever.get_transcript(video_id) if self.data_retriever else self.get_transcript(video_id)

                if not transcript:
                    print(f"No transcript for video: {video['title']}")
                    failed_videos.append({"id": video_id, "title": video["title"], "reason": "No transcript available"})
                    continue

                report = self.analyze_transcript(video, transcript)
                if report:
                    valid_videos.append(video)
                else:
                    failed_videos.append({"id": video_id, "title": video["title"], "reason": "Analysis failed"})
            except Exception as e:
                print(f"Error analyzing video {video['title']}: {e}")
                failed_videos.append({"id": video_id, "title": video["title"], "reason": str(e)})

        if not valid_videos:
            print("No valid videos available for digest generation")
            return {
                "title": title or "AI Video Digest",
                "date": datetime.now().isoformat(),
                "error": "No valid videos available for analysis",
                "failed_videos": failed_videos if failed_videos else []
            }

        print(f"Generating digest for {len(valid_videos)} videos")
        print(f"Skipped {skipped_videos} already analyzed videos")
        if failed_videos:
            print(f"Failed to analyze {len(failed_videos)} videos")

        # Generate unique digest ID from timestamp
        digest_id = f"digest_{int(time.time())}"

        # Create the digest prompt
        prompt = f"""You are an expert content analyst creating a comprehensive digest of YouTube videos across multiple themes including Science & Education, Tech & Programming, Fitness & Health, AI & Machine Learning, General News, and Tech News & Reviews.

Your task is to analyze these videos and create an insightful digest that captures key developments, trends, and insights across different content categories.

Videos analyzed:
{json.dumps(valid_videos, indent=2)}

Please provide a structured analysis in the following JSON format:

{{
    "title": "{title or 'Content Digest'}",
    "date": "{datetime.now().strftime('%Y-%m-%d')}",
    "executive_summary": "2-3 paragraphs summarizing the most important developments and insights across all categories",

    "content_categories": [
        {{
            "category": "Category name",
            "key_developments": [
                {{
                    "title": "Development title",
                    "description": "Detailed explanation",
                    "impact": "Potential impact or significance",
                    "source_videos": ["Video titles"]
                }}
            ],
            "emerging_trends": [
                {{
                    "trend": "Trend name",
                    "description": "Trend explanation",
                    "evidence": ["Supporting evidence"],
                    "implications": "Potential implications"
                }}
            ]
        }}
    ],

    "cross_category_insights": [
        {{
            "topic": "Topic spanning multiple categories",
            "description": "Connection explanation",
            "categories": ["Related categories"],
            "key_points": ["Important points"],
            "source_videos": ["Video titles"]
        }}
    ],

    "featured_content": {{
        "title": "Most significant topic/development",
        "description": "Detailed description",
        "key_points": ["Important points"],
        "current_state": "Current state of development",
        "future_potential": "Future implications",
        "related_videos": ["Video titles"]
    }},

    "notable_insights": [
        {{
            "category": "Content category",
            "insight": "Key insight",
            "explanation": "Why this is important",
            "practical_value": "How this can be applied",
            "source": "Source video(s)"
        }}
    ],

    "video_summaries": [
        {{
            "video_id": "Video ID",
            "video_title": "Video title",
            "channel_title": "Channel name",
            "category": "Primary content category",
            "highlights": "Key content summary",
            "main_topics": ["Main topics"],
            "key_points": ["Key points"],
            "practical_takeaways": ["Actionable insights"],
            "relevance": "High/Medium/Low"
        }}
    ],

    "recommendations": [
        {{
            "audience": "Target audience",
            "recommended_videos": [
                {{
                    "title": "Video title",
                    "reason": "Why this is relevant"
                }}
            ],
            "key_themes": ["Relevant themes"],
            "practical_value": "Benefits for this audience"
        }}
    ]
}}

Important guidelines:
1. Ensure each category has at least 2-3 key developments and trends
2. Focus on practical insights and actionable takeaways
3. Highlight connections between different content categories
4. Include specific examples and evidence from the videos
5. Maintain a balance between technical depth and accessibility
6. Consider implications for different audience types

Return ONLY the JSON object, no additional text."""

        # Call the Anthropic API
        response = self._call_claude_api(prompt)
        if not response:
            return None

        try:
            # Parse the response and extract JSON
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                digest = json.loads(json_str)
            else:
                raise json.JSONDecodeError("No valid JSON found", response, 0)

            # Ensure all sections are present with proper structure
            digest.setdefault('title', title or 'Content Digest')
            digest.setdefault('date', datetime.now().strftime('%Y-%m-%d'))
            digest.setdefault('executive_summary', 'No summary available')
            digest.setdefault('content_categories', [])
            digest.setdefault('cross_category_insights', [])
            digest.setdefault('featured_content', {})
            digest.setdefault('notable_insights', [])
            digest.setdefault('video_summaries', [])
            digest.setdefault('recommendations', [])

            # Format video summaries with consistent structure
            formatted_summaries = []
            for i, video in enumerate(valid_videos):
                summary = {
                    'video_id': video['id'],
                    'video_title': video['title'],
                    'channel_title': video.get('channel_title', 'Unknown'),
                    'category': 'General',  # Default category
                    'highlights': 'No highlights available',
                    'main_topics': [],
                    'key_points': [],
                    'practical_takeaways': [],
                    'relevance': 'Medium'
                }

                # Update with any existing summary data
                if i < len(digest['video_summaries']):
                    existing = digest['video_summaries'][i]
                    summary.update({k: v for k, v in existing.items() if v})

                formatted_summaries.append(summary)

            digest['video_summaries'] = formatted_summaries

            # Add metadata
            digest['id'] = digest_id
            digest['generated_at'] = datetime.now().isoformat()
            digest['video_count'] = len(valid_videos)
            digest['videos_analyzed'] = [{'id': v['id'], 'title': v['title']} for v in valid_videos]
            if failed_videos:
                digest['failed_videos'] = failed_videos

            # Save the digest
            digest_file = os.path.join(self.data_dir, f"{digest_id}.json")
            with open(digest_file, 'w', encoding='utf-8') as f:
                json.dump(digest, f, indent=2)

            return digest

        except Exception as e:
            print(f"Error generating digest: {e}")
            return None

    def _call_claude_api(self, prompt: str) -> Optional[str]:
        """
        Call the Anthropic API with improved error handling and retry logic.

        Args:
            prompt: The prompt to send to the API.

        Returns:
            API response text or None if the call failed.
        """
        import time
        import ssl
        import requests
        from requests.adapters import HTTPAdapter

        max_retries = 3
        retry_delay = 2  # seconds
        response_text = None

        # Enhance the prompt to emphasize JSON format if it appears to be a JSON request
        if "JSON format" in prompt or "json format" in prompt:
            # Add JSON-specific instructions to the end of the prompt
            json_instruction = "\n\nIMPORTANT: Your response must be ONLY the requested JSON object with no additional text before or after it. Start your response with the opening brace '{' and end with the closing brace '}'."
            prompt = prompt + json_instruction

        for attempt in range(max_retries):
            try:
                print(f"Calling Anthropic API - Attempt {attempt + 1}/{max_retries}")

                # Create session with custom adapter and longer timeout
                session = requests.Session()
                adapter = TlsAdapter()
                adapter.max_retries = 3  # Add retries at the adapter level
                session.mount('https://', adapter)

                # Prepare headers
                headers = {
                    "x-api-key": config.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }

                # Use completions API (Claude 2)
                data = {
                    "model": "claude-2.0",
                    "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                    "max_tokens_to_sample": 8000,
                    "temperature": 0.0
                }

                # Make the request with increased timeout
                response = session.post(
                    "https://api.anthropic.com/v1/complete",
                    headers=headers,
                    json=data,
                    timeout=90  # Increase timeout to 90 seconds
                )

                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("completion", "")
                    print(f"Direct API call successful! Received {len(response_text)} chars")
                    return response_text
                else:
                    print(f"Direct API call failed with status {response.status_code}: {response.text}")
                    if response.status_code == 429:  # Rate limit
                        retry_delay = min(retry_delay * 2, 30)  # Exponential backoff capped at 30 seconds
                        time.sleep(retry_delay)
                        continue
                    raise Exception(f"API error: {response.text}")

            except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as timeout_err:
                print(f"Timeout error (attempt {attempt+1}/{max_retries}): {timeout_err}")
                if attempt < max_retries - 1:
                    retry_delay = min(retry_delay * 2, 30)  # Exponential backoff capped at 30 seconds
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Max timeout retries exceeded.")
                    return None

            except ssl.SSLError as ssl_err:
                print(f"SSL Error (attempt {attempt+1}/{max_retries}): {ssl_err}")
                if attempt < max_retries - 1:
                    retry_delay = min(retry_delay * 2, 30)  # Exponential backoff capped at 30 seconds
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Max SSL error retries exceeded.")
                    return None

            except Exception as e:
                print(f"Error calling Anthropic API (attempt {attempt+1}/{max_retries}): {e}")
                if "401" in str(e) or "authentication" in str(e).lower():
                    print("\nAuthentication error with the Anthropic API.")
                    print("Please check your API key in the .env file and ensure it is valid.")
                    return None

                if attempt < max_retries - 1:
                    retry_delay = min(retry_delay * 2, 30)  # Exponential backoff capped at 30 seconds
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Max API error retries exceeded.")
                    return None

        return response_text
