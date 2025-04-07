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

        # Initialize vector store with error handling
        self.vector_store = None
        try:
            from src.vector_store import VectorStore
            self.vector_store = VectorStore()
            print("Vector store initialized successfully")
        except Exception as e:
            print(f"Warning: Vector store initialization failed (this is okay, will continue without it): {str(e)}")
            self.vector_store = None

    def get_transcript(self, video_id: str) -> Optional[str]:
        """
        Get transcript for a YouTube video, trying ['en', 'fr'].

        Args:
            video_id: YouTube video ID.

        Returns:
            Transcript text or None if unavailable.
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

            # List available transcripts first
            transcript_list_details = YouTubeTranscriptApi.list_transcripts(video_id)

            transcript = None
            transcript_list = None
            languages_to_try = ['en', 'fr']
            found_lang = None

            for lang in languages_to_try:
                try:
                    # Try fetching the transcript for the current language
                    transcript = transcript_list_details.find_transcript([lang])
                    transcript_list = transcript.fetch()
                    found_lang = lang
                    print(f"Found transcript in language: {found_lang} for video {video_id}")
                    break # Stop trying once a transcript is found
                except NoTranscriptFound:
                    continue # Try the next language in the list

            if not transcript or not transcript_list:
                 print(f"No transcript found for video {video_id} in any of the requested languages: {languages_to_try}")
                 return None

            transcript_text = " ".join([entry["text"] for entry in transcript_list])

            # Save transcript to file
            transcript_file = os.path.join(self.data_dir, f"{video_id}_transcript.txt")
            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(transcript_text)

            return transcript_text

        except TranscriptsDisabled as e:
            print(f"Transcripts are disabled for video {video_id}: {e}")
            return None
        except NoTranscriptFound as e:
             print(f"Could not find any transcripts for video {video_id} using list_transcripts: {e}")
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
        prompt = f"""You are a detailed video content analyzer. Analyze this YouTube video transcript and provide a comprehensive analysis in JSON format.

Video Title: {video['title']}
Video ID: {video_id}

Transcript:
{transcript[:50000]}  # Truncate to avoid token limits

Analyze the content and provide a detailed response in this EXACT JSON format:
{{
    "main_topics": [
        "Topic 1 with specific detail",
        "Topic 2 with specific detail",
        "Topic 3 with specific detail"
    ],
    "key_points": [
        "Detailed point 1 with specific information",
        "Detailed point 2 with specific information",
        "Detailed point 3 with specific information",
        "Detailed point 4 with specific information",
        "Detailed point 5 with specific information"
    ],
    "technical_details": [
        "Specific technical detail 1",
        "Specific technical detail 2",
        "Specific technical detail 3"
    ],
    "technologies_mentioned": [
        "Specific technology 1",
        "Specific technology 2",
        "Specific technology 3"
    ],
    "overall_summary": "A detailed 2-3 paragraph summary that captures the main message, key insights, and value of the content. Be specific and include actual examples from the video.",
    "important_facts": [
        "Specific fact 1 with actual data/quote",
        "Specific fact 2 with actual data/quote",
        "Specific fact 3 with actual data/quote",
        "Specific fact 4 with actual data/quote",
        "Specific fact 5 with actual data/quote"
    ],
    "examples_and_stories": [
        "Detailed example 1 from the video",
        "Detailed example 2 from the video",
        "Detailed example 3 from the video"
    ],
    "important_segments": [
        "Key segment 1 with main points",
        "Key segment 2 with main points",
        "Key segment 3 with main points"
    ],
    "tone_and_style": "Detailed description of the speaker's presentation style and approach",
    "target_audience": [
        "Specific audience type 1",
        "Specific audience type 2",
        "Specific audience type 3"
    ],
    "content_quality": "Detailed assessment of the content's depth, accuracy, and practical value"
}}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no other text, no markdown, no explanations
2. Every field MUST contain actual content from the video - no placeholders
3. Lists must contain at least 3 detailed items
4. Examples must be specific moments or demonstrations from the video
5. Facts must include actual quotes, numbers, or specific information
6. Summary must be detailed and reference actual content
7. Start response with '{{' and end with '}}'"""

        # Call the Anthropic API
        response = self._call_claude_api(prompt)
        if not response:
            print(f"No response received for video: {video['title']}")
            return None

        try:
            # Extract JSON from the response
            json_match = re.search(r'(\{[\s\S]*\})', response)
            if json_match:
                json_str = json_match.group(1)
                analysis = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

            # Create report with consistent structure
            report = {
                "video_id": video_id,
                "video_title": video["title"],
                "title": video["title"],
                "analysis_date": datetime.now().isoformat(),
                "analysis": {
                    "main_topics": analysis.get("main_topics", []),
                    "key_points": analysis.get("key_points", []),
                    "technical_details": analysis.get("technical_details", []),
                    "technologies_mentioned": analysis.get("technologies_mentioned", []),
                    "overall_summary": analysis.get("overall_summary", ""),
                    "summary": analysis.get("overall_summary", ""),
                    "important_facts": analysis.get("important_facts", []),
                    "examples_and_stories": analysis.get("examples_and_stories", []),
                    "examples_and_segments": analysis.get("examples_and_stories", []),
                    "important_segments": analysis.get("important_segments", []),
                    "tone_and_style": analysis.get("tone_and_style", ""),
                    "content_quality": analysis.get("content_quality", ""),
                    "target_audience": analysis.get("target_audience", [])
                }
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

        except Exception as e:
            print(f"Error analyzing transcript for video {video['title']}: {e}")
            print(f"Raw response excerpt: {response[:200]}...")
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
        Index a report in the vector store if available.

        Args:
            report: Report data dictionary.
        """
        if not self.vector_store:
            return  # Skip if vector store is not available

        try:
            print(f"Indexing report for video {report['video_id']} in vector store...")

            # Ensure the report has the required fields in the correct structure
            formatted_report = {
                "video_id": report["video_id"],
                "video_title": report.get("video_title", report.get("title", "Unknown")),
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
            print(f"Warning: Error indexing report in vector store (continuing without indexing): {e}")

    def _index_transcript_in_vector_store(self, video_id: str, video_title: str, transcript_text: str) -> None:
        """Index transcript in vector store for future queries if available."""
        if not self.vector_store:
            return  # Skip if vector store is not available

        try:
            self.vector_store.index_transcript(video_id, video_title, transcript_text)
        except Exception as e:
            print(f"Warning: Error indexing transcript in vector store (continuing without indexing): {e}")

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
