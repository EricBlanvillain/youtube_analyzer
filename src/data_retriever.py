"""
Data retriever for YouTube Analyzer.
This module handles interactions with the YouTube API to retrieve
channel information and video data.
"""
from typing import List, Dict, Any, Optional, Tuple
import os
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from utils.config import config

class DataRetriever:
    """Agent for retrieving data from YouTube API."""

    def __init__(self):
        """Initialize the YouTube API client."""
        self.youtube = build(
            "youtube", "v3", developerKey=config.youtube_api_key
        )

    def get_channel_id(self, channel_name: str) -> Optional[str]:
        """
        Get the channel ID from a channel name.

        Args:
            channel_name: The name of the YouTube channel.

        Returns:
            The channel ID if found, None otherwise.
        """
        try:
            search_response = self.youtube.search().list(
                q=channel_name,
                type="channel",
                part="id,snippet",
                maxResults=1
            ).execute()

            if not search_response.get("items"):
                print(f"No channel found with name: {channel_name}")
                return None

            return search_response["items"][0]["id"]["channelId"]
        except HttpError as e:
            print(f"An error occurred while searching for the channel: {e}")
            return None

    def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a YouTube channel.

        Args:
            channel_id: The ID of the YouTube channel.

        Returns:
            Dictionary with channel information or None if not found.
        """
        try:
            channel_response = self.youtube.channels().list(
                part="snippet,statistics",
                id=channel_id
            ).execute()

            if not channel_response.get("items"):
                print(f"No channel found with ID: {channel_id}")
                return None

            channel = channel_response["items"][0]
            return {
                "id": channel_id,
                "title": channel["snippet"]["title"],
                "description": channel["snippet"]["description"],
                "subscriber_count": channel["statistics"]["subscriberCount"],
                "view_count": channel["statistics"]["viewCount"],
                "video_count": channel["statistics"]["videoCount"]
            }
        except HttpError as e:
            print(f"An error occurred while retrieving channel info: {e}")
            return None

    def get_recent_videos(self, channel_id: str, max_results: int = 30) -> List[Dict[str, Any]]:
        """
        Get a list of recent videos from a channel, excluding shorts.

        Args:
            channel_id: The ID of the YouTube channel.
            max_results: Maximum number of results to fetch initially.

        Returns:
            List of video information dictionaries.
        """
        try:
            # First, get video IDs from the channel
            search_response = self.youtube.search().list(
                channelId=channel_id,
                part="id",
                order="date",
                maxResults=max_results,
                type="video"
            ).execute()

            if not search_response.get("items"):
                print(f"No videos found for channel: {channel_id}")
                return []

            # Extract video IDs
            video_ids = [item["id"]["videoId"] for item in search_response["items"]]

            # Get detailed information about the videos
            videos_response = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=",".join(video_ids)
            ).execute()

            # Process and filter videos
            videos = []
            for video in videos_response["items"]:
                # Parse duration to seconds
                duration = video["contentDetails"]["duration"]
                duration_seconds = self._parse_duration(duration)

                # Filter out shorts (videos < 60 seconds)
                if duration_seconds < 60:
                    continue

                videos.append({
                    "id": video["id"],
                    "title": video["snippet"]["title"],
                    "published_at": video["snippet"]["publishedAt"],
                    "duration": duration,
                    "duration_seconds": duration_seconds,
                    "view_count": video["statistics"].get("viewCount", "0"),
                    "like_count": video["statistics"].get("likeCount", "0"),
                    "comment_count": video["statistics"].get("commentCount", "0")
                })

                # Stop if we have enough long videos
                if len(videos) >= config.max_videos:
                    break

            return videos[:config.max_videos]
        except HttpError as e:
            print(f"An error occurred while retrieving videos: {e}")
            return []

    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse ISO 8601 duration format to seconds.

        Args:
            duration_str: ISO 8601 duration string (e.g., 'PT5M30S').

        Returns:
            Duration in seconds.
        """
        # Remove 'PT' prefix
        duration = duration_str[2:]

        hours = 0
        minutes = 0
        seconds = 0

        # Extract hours
        if 'H' in duration:
            hours_part, duration = duration.split('H')
            hours = int(hours_part)

        # Extract minutes
        if 'M' in duration:
            minutes_part, duration = duration.split('M')
            minutes = int(minutes_part)

        # Extract seconds
        if 'S' in duration:
            seconds = int(duration.rstrip('S'))

        return hours * 3600 + minutes * 60 + seconds

    def get_channel_and_videos(self, channel_name: str) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Get channel information and recent videos.

        Args:
            channel_name: Name of the YouTube channel.

        Returns:
            Tuple of (channel_info, videos) where videos is a list of video dictionaries.
        """
        channel_id = self.get_channel_id(channel_name)
        if not channel_id:
            return None, []

        channel_info = self.get_channel_info(channel_id)
        if not channel_info:
            return None, []

        videos = self.get_recent_videos(channel_id)
        return channel_info, videos

    def get_multi_channel_videos(self, channel_names: List[str], max_videos_per_channel: int = 5) -> List[Tuple[Dict[str, Any], List[Dict[str, Any]]]]:
        """
        Get channel information and recent videos for multiple channels.

        Args:
            channel_names: List of YouTube channel names.
            max_videos_per_channel: Maximum number of videos to retrieve per channel.

        Returns:
            List of tuples containing (channel_info, channel_videos) for each channel.
        """
        results = []

        for channel_name in channel_names:
            # Get channel info and videos
            channel_id = self.get_channel_id(channel_name)
            if not channel_id:
                print(f"Could not retrieve channel ID for: {channel_name}")
                continue

            channel_info = self.get_channel_info(channel_id)
            if not channel_info:
                print(f"Could not retrieve channel info for: {channel_name}")
                continue

            # Get limited number of recent videos for this channel
            videos = self.get_recent_videos(channel_id, max_results=max_videos_per_channel)
            if videos:
                results.append((channel_info, videos))
            else:
                print(f"No suitable videos found for channel: {channel_info['title']}")

        return results

    def get_transcript(self, video_id: str) -> Optional[str]:
        """
        Get transcript for a YouTube video.

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
            languages_to_try = ['en', 'fr']
            found_lang = None

            for lang in languages_to_try:
                try:
                    # Try fetching the transcript for the current language
                    # find_transcript will check both manual and generated
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

            # Combine all transcript entries into a single text
            transcript_text = " ".join([entry["text"] for entry in transcript_list])
            return transcript_text

        except TranscriptsDisabled as e:
            print(f"Transcripts are disabled for video {video_id}: {e}")
            return None
        # NoTranscriptFound should be handled by the loop now,
        # but we keep it here for safety in case list_transcripts fails in a specific way
        except NoTranscriptFound as e:
             print(f"Could not find any transcripts for video {video_id} using list_transcripts: {e}")
             return None
        except Exception as e:
            print(f"Error retrieving transcript for video {video_id}: {e}")
            return None
