"""
QA agent for YouTube Analyzer.
This module handles answering user questions about analyzed videos
using stored reports.
"""
from typing import List, Dict, Any, Optional
import os
import json
import anthropic
import time

from utils.config import config
from src.vector_store import VectorStore

class QAAgent:
    """Agent for answering questions about analyzed videos."""

    def __init__(self):
        """Initialize the QA agent with Anthropic client and vector store."""
        # Try to handle different versions of the Anthropic API
        self.anthropic_client = None
        self.api_version = "unknown"

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
        except (AttributeError, TypeError):
            # Fall back to older version (Client)
            try:
                self.anthropic_client = anthropic.Client(api_key=config.anthropic_api_key)
                self.api_version = "client"
            except Exception as e:
                print(f"Error initializing Anthropic client: {e}")
                raise

        print(f"Using Anthropic API version: {self.api_version}")

        # Initialize vector store
        self.vector_store = VectorStore()

        # Set data directory
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

    def list_available_reports(self) -> List[Dict[str, Any]]:
        """
        List all available analysis reports.

        Returns:
            List of report metadata.
        """
        reports = []

        # Check if data directory exists
        if not os.path.exists(self.data_dir):
            return reports

        # Find all report files
        for filename in os.listdir(self.data_dir):
            if filename.endswith("_report.json"):
                report_path = os.path.join(self.data_dir, filename)
                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        report = json.load(f)
                        reports.append({
                            "video_id": report["video_id"],
                            "video_title": report["video_title"],
                            "analysis_timestamp": report["analysis_timestamp"],
                            "report_file": filename
                        })
                except Exception as e:
                    print(f"Error reading report {filename}: {e}")

        return reports

    def get_report_by_id(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific report by video ID.

        Args:
            video_id: YouTube video ID.

        Returns:
            Report data or None if not found.
        """
        report_path = os.path.join(self.data_dir, f"{video_id}_report.json")

        if not os.path.exists(report_path):
            print(f"No report found for video ID: {video_id}")
            return None

        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)

                # Check if this report is indexed in vector store
                self._ensure_report_indexed(report)

                return report
        except Exception as e:
            print(f"Error reading report for video {video_id}: {e}")
            return None

    def get_transcript_by_id(self, video_id: str) -> Optional[str]:
        """
        Get a transcript by video ID.

        Args:
            video_id: YouTube video ID.

        Returns:
            Transcript text or None if not found.
        """
        transcript_path = os.path.join(self.data_dir, f"{video_id}_transcript.txt")

        if not os.path.exists(transcript_path):
            print(f"No transcript found for video ID: {video_id}")
            return None

        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                transcript_text = f.read()

                # Get the report to get the video title
                report = self.get_report_by_id(video_id)
                if report:
                    # Check if this transcript is indexed in vector store
                    self._ensure_transcript_indexed(video_id, report["video_title"], transcript_text)

                return transcript_text
        except Exception as e:
            print(f"Error reading transcript for video {video_id}: {e}")
            return None

    def _ensure_report_indexed(self, report: Dict[str, Any]) -> None:
        """
        Make sure a report is indexed in the vector store.

        Args:
            report: Report data dictionary.
        """
        # A simple heuristic to check if it's indexed: try to retrieve it
        video_id = report["video_id"]
        test_query = f"Video {report['video_title']}"
        results = self.vector_store.retrieve_relevant_chunks(
            query=test_query,
            n_results=1,
            include_reports=True,
            include_transcripts=False,
            video_ids=[video_id]
        )

        # If no results found, index the report
        if not results:
            print(f"Indexing report for video {video_id} in vector store...")
            self.vector_store.index_report(report)

    def _ensure_transcript_indexed(self, video_id: str, video_title: str, transcript_text: str) -> None:
        """
        Make sure a transcript is indexed in the vector store.

        Args:
            video_id: YouTube video ID.
            video_title: Video title.
            transcript_text: Transcript text.
        """
        # A simple heuristic to check if it's indexed: try to retrieve it
        test_query = f"Transcript {video_title}"
        results = self.vector_store.retrieve_relevant_chunks(
            query=test_query,
            n_results=1,
            include_reports=False,
            include_transcripts=True,
            video_ids=[video_id]
        )

        # If no results found, index the transcript
        if not results:
            print(f"Indexing transcript for video {video_id} in vector store...")
            self.vector_store.index_transcript(video_id, video_title, transcript_text)

    def answer_question(self, question: str, video_ids: Optional[List[str]] = None) -> str:
        """
        Answer a question about analyzed videos.

        Args:
            question: The user's question.
            video_ids: List of specific video IDs to consider or None for all.

        Returns:
            Answer to the question.
        """
        # Start timing for performance tracking
        start_time = time.time()
        print(f"Processing question: {question}")

        # First make sure all reports and transcripts are indexed
        if video_ids:
            # Ensure specific videos are indexed
            for video_id in video_ids:
                report = self.get_report_by_id(video_id)
                if report:
                    self._ensure_report_indexed(report)
                    # Also index transcript if available
                    transcript = self.get_transcript_by_id(video_id)
                    if transcript:
                        self._ensure_transcript_indexed(video_id, report["video_title"], transcript)
        else:
            # Get all available reports
            report_metadata = self.list_available_reports()
            for meta in report_metadata:
                video_id = meta["video_id"]
                report = self.get_report_by_id(video_id)
                if report:
                    self._ensure_report_indexed(report)
                    # Also index transcript if available
                    transcript = self.get_transcript_by_id(video_id)
                    if transcript:
                        self._ensure_transcript_indexed(video_id, report["video_title"], transcript)

        # Check if we have any reports
        reports_available = len(self.list_available_reports()) > 0
        if not reports_available:
            return "No analyzed videos available to answer your question."

        # Use vector search to retrieve relevant information
        print("Retrieving relevant information using vector search...")
        context = self.vector_store.get_context_for_query(question, video_ids)

        # Check if we have any context
        if context == "No relevant information found.":
            return "I couldn't find any relevant information to answer your question in the analyzed videos."

        # Print time taken for retrieval
        retrieval_time = time.time() - start_time
        print(f"Retrieved relevant context in {retrieval_time:.2f} seconds")

        # Analyze the question to determine if we need specific details
        needs_specific_details = any(term in question.lower() for term in [
            "specific", "exactly", "precisely", "detail", "mention", "reference", "quote", "number",
            "statistic", "percentage", "date", "when", "how many", "how much", "where", "who", "which"
        ])

        # Prepare prompt for Claude
        prompt = f"""
        You are Claude, an AI assistant specialized in analyzing and answering questions about YouTube content.

        TASK CONTEXT:
        A user is asking a question about YouTube videos that have been analyzed. Your role is to provide a helpful, informative response based on the analysis reports and transcript excerpts available.

        USER QUESTION:
        {question}

        AVAILABLE INFORMATION (Retrieved using semantic search):
        {context}

        RESPONSE REQUIREMENTS:
        1. Provide a direct, concise answer that clearly addresses the user's question
        2. Reference specific videos and their content when relevant to the answer
        3. Structure your response with appropriate paragraphs and bullet points when needed
        4. If multiple videos provide relevant information, synthesize it for a comprehensive answer
        5. If the information needed to answer the question is not available in the reports, clearly state this
        6. Use a helpful, conversational tone appropriate for someone seeking knowledge
        7. For specific facts, quotes, or statistical questions, provide as precise information as possible
        8. When appropriate, indicate which video(s) contained the information you're sharing

        IMPORTANT GUIDELINES:
        - Only use information explicitly provided in the analysis reports and transcript excerpts
        - If asked for specific details that might be in the full transcript but not in your context, mention that more complete information may be available in the full video
        - Do not make assumptions about video content beyond what is in the provided information
        - If asked for opinions, indicate that you're sharing insights based on the analysis, not personal views
        - If asked to compare videos, focus on objective differences in content, style, and approach
        - Maintain a neutral, balanced perspective when discussing controversial topics
        """

        # If the question seems to need very specific details, add this to the prompt
        if needs_specific_details:
            prompt += """

            SPECIFIC DETAIL REQUEST DETECTED:
            The user seems to be asking for specific details. Focus on providing the most precise information available in the reports and transcript excerpts. If exact details aren't available in your context, clearly state this limitation while providing the closest related information that is available.
            """

        try:
            # Start timing for LLM call
            llm_start_time = time.time()

            # Call Anthropic API using the appropriate method based on version
            if self.api_version == "messages":
                # Newest API with messages.create
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    temperature=0.0,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                answer = response.content[0].text.strip()
            elif self.api_version == "completions":
                # Newer API with completions
                response = self.anthropic_client.completions.create(
                    model="claude-2.0",
                    prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
                    max_tokens_to_sample=4000,
                    temperature=0,
                )
                answer = response.completion.strip()
            else:
                # Old API (Client class with completion)
                response = self.anthropic_client.completion(
                    prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
                    model="claude-2.0",
                    max_tokens_to_sample=4000,
                    temperature=0.0,
                )
                answer = response.completion.strip()

            # Print time taken for LLM call
            llm_time = time.time() - llm_start_time
            print(f"LLM response generated in {llm_time:.2f} seconds")

            # Print total time
            total_time = time.time() - start_time
            print(f"Total question answering time: {total_time:.2f} seconds")

            return answer

        except Exception as e:
            print(f"Error answering question: {e}")
            return f"Sorry, I encountered an error while processing your question: {str(e)}"
