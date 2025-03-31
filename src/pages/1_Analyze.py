#!/usr/bin/env python3
"""
Streamlit page for YouTube video analysis.
This page allows users to search for channels, browse videos, and perform analysis.
"""
import streamlit as st
import pandas as pd
import time
from datetime import datetime

from src.orchestrator import WorkflowOrchestrator
from utils.config import config

# Initialize session state variables if they don't exist
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = WorkflowOrchestrator()
if 'channel_info' not in st.session_state:
    st.session_state.channel_info = None
if 'videos' not in st.session_state:
    st.session_state.videos = []
if 'selected_videos' not in st.session_state:
    st.session_state.selected_videos = []
if 'analyzed_videos' not in st.session_state:
    st.session_state.analyzed_videos = []
if 'reports' not in st.session_state:
    st.session_state.reports = []
if 'selected_channel_name' not in st.session_state:
    st.session_state.selected_channel_name = None
if 'showing_video_details' not in st.session_state:
    st.session_state.showing_video_details = None
if 'show_pre_analysis_details' not in st.session_state:
    st.session_state.show_pre_analysis_details = None
if 'recent_searches' not in st.session_state:
    st.session_state.recent_searches = []

# Utility functions
def format_subscribers(count):
    """Format subscriber count for better readability."""
    count = int(count)
    if count >= 1000000:
        return f"{count/1000000:.1f}M"
    elif count >= 1000:
        return f"{count/1000:.1f}K"
    else:
        return str(count)

def format_duration(seconds):
    """Format duration in seconds to minutes:seconds."""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"

def toggle_video_details(video_id=None):
    """Toggle the display of video details."""
    if video_id == st.session_state.showing_video_details:
        # If we're toggling the same video, hide it
        st.session_state.showing_video_details = None
    else:
        # Show the new video
        st.session_state.showing_video_details = video_id

def search_channel():
    """Search for a YouTube channel and display its videos."""
    # Check if we have a selected channel name from popular channels or favorites
    if st.session_state.selected_channel_name:
        channel_name = st.session_state.selected_channel_name
        # Reset the selected channel name
        st.session_state.selected_channel_name = None
    else:
        channel_name = st.session_state.channel_name

    if not channel_name:
        st.error("Please enter a channel name or select one from the popular channels.")
        return

    # Display a progress message with spinner
    with st.spinner(f"Searching for channel: {channel_name}"):
        try:
            # Get channel info and videos
            channel_info, videos = st.session_state.orchestrator.data_retriever.get_channel_and_videos(channel_name)

            # Handle errors
            if not channel_info:
                st.error(f"Could not find channel: {channel_name}")
                st.info("Please verify the channel name and try again. Note that some channels may have different official names than their display names.")
                return

            if not videos:
                st.warning(f"No suitable videos found for channel: {channel_info['title']}")
                st.info("This could be because the channel doesn't have any videos with English transcripts available, or all videos are shorts/livestreams.")
                return

            # Success message
            st.success(f"Found channel: {channel_info['title']} with {len(videos)} videos")

            # Store in session state
            st.session_state.channel_info = channel_info
            st.session_state.videos = videos

            # Add to recent searches if not already there
            if 'recent_searches' not in st.session_state:
                st.session_state.recent_searches = []

            # Add the channel to recent searches (avoid duplicates)
            if channel_name not in st.session_state.recent_searches:
                st.session_state.recent_searches.append(channel_name)

            # Keep only the last 10 searches
            if len(st.session_state.recent_searches) > 10:
                st.session_state.recent_searches = st.session_state.recent_searches[-10:]

            # Clear any previous analysis results when changing channels
            if 'analyzed_videos' in st.session_state:
                st.session_state.analyzed_videos = []

        except Exception as e:
            st.error(f"An error occurred while searching for the channel: {str(e)}")
            st.info("This might be due to API rate limits or connectivity issues. Please try again later.")

# Callback function for when a popular channel is selected
def select_popular_channel(channel_name):
    st.session_state.selected_channel_name = channel_name
    search_channel()

# Callback function for when a favorite channel is selected
def select_favorite_channel(channel_name):
    st.session_state.selected_channel_name = channel_name
    search_channel()

def analyze_selected_videos():
    """Analyze the videos selected by the user."""
    selected_indices = st.session_state.video_selection

    if not selected_indices:
        st.error("Please select at least one video to analyze.")
        return

    # Check if we're using filtered videos (if filter was applied)
    if 'filtered_videos' in st.session_state:
        # Map the selected indices to the actual video indices
        actual_indices = [st.session_state.filtered_videos[i] for i in selected_indices if i < len(st.session_state.filtered_videos)]
        # Get selected videos
        selected_videos = [st.session_state.videos[i] for i in actual_indices]
    else:
        # No filtering, use indices directly
        selected_videos = [st.session_state.videos[i] for i in selected_indices]

    st.session_state.selected_videos = selected_videos

    # Process each video
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, video in enumerate(selected_videos):
        progress = i / len(selected_videos)
        progress_bar.progress(progress)
        status_text.text(f"Processing video {i+1}/{len(selected_videos)}: {video['title']}")

        # Get transcript
        transcript = st.session_state.orchestrator.report_generator.get_transcript(video['id'])

        if not transcript:
            st.warning(f"Could not retrieve transcript for: {video['title']}")
            continue

        # Analyze transcript
        report = st.session_state.orchestrator.report_generator.analyze_transcript(video, transcript)

        if report:
            st.session_state.analyzed_videos.append(report)

    # Complete the progress bar
    progress_bar.progress(1.0)
    status_text.text(f"Completed analyzing {len(selected_videos)} videos.")

    # Update reports list
    st.session_state.reports = st.session_state.orchestrator.qa_agent.list_available_reports()

# Main function for the Analyze page
def display_analyze_page():
    st.markdown('<div class="main-title">YouTube Channel Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Search for YouTube channels, browse videos, and analyze content</div>', unsafe_allow_html=True)

    # Check API keys first
    missing_keys = []
    if not config.youtube_api_key:
        missing_keys.append("YouTube API Key")
    if not config.anthropic_api_key:
        missing_keys.append("Anthropic API Key")

    if missing_keys:
        st.error(f"Missing required API keys: {', '.join(missing_keys)}")
        st.info("Please add these keys to your .env file and restart the application.")
        return

    # Channel search tabs
    search_tab, popular_tab, favorites_tab = st.tabs(["Search by Name", "Browse Popular Channels", "My Favorites"])

    with search_tab:
        # Channel search form
        st.markdown('<div class="section-header">Search for a YouTube Channel</div>', unsafe_allow_html=True)

        # Add custom CSS for better form alignment
        st.markdown("""
        <style>
        .search-container {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
        }
        .search-input {
            flex: 1;
        }
        .search-button button {
            height: 100%;
            margin-top: 24px; /* Adjust based on Streamlit's label height */
        }
        </style>
        """, unsafe_allow_html=True)

        # Start the form container
        st.markdown('<div class="search-container">', unsafe_allow_html=True)

        # Input field container
        st.markdown('<div class="search-input">', unsafe_allow_html=True)
        channel_name = st.text_input("Enter channel name:", key="channel_name",
                       placeholder="e.g., 'Computerphile' or 'DeepLearningAI'")
        st.markdown('</div>', unsafe_allow_html=True)

        # Button container
        st.markdown('<div class="search-button">', unsafe_allow_html=True)
        if st.button("Search", key="search_button"):
            search_channel()
        st.markdown('</div>', unsafe_allow_html=True)

        # Close the form container
        st.markdown('</div>', unsafe_allow_html=True)

        # Show recent searches if available
        if st.session_state.recent_searches:
            st.markdown("##### Recent Searches")
            cols = st.columns(min(5, len(st.session_state.recent_searches)))
            for i, channel in enumerate(st.session_state.recent_searches[-5:]):
                with cols[i % 5]:
                    if st.button(channel, key=f"recent_{i}"):
                        st.session_state.channel_name = channel
                        search_channel()

    with popular_tab:
        st.markdown('<div class="section-header">Popular YouTube Channels</div>', unsafe_allow_html=True)

        # Group channels by category with expanded categories
        categories = {
            "Tech & AI": [
                "DeepLearningAI", "TwoMinutePapers", "YannicKilcher",
                "Computerphile", "3Blue1Brown", "StatQuestwithJoshStarmer",
                "CodeBullet", "SentdexSentdex", "LexFridman"
            ],
            "Science & Education": [
                "Veritasium", "Kurzgesagt", "CrashCourse",
                "SciShow", "MinutePhysics", "VSauce",
                "SmartEveryday", "TED", "ThoughtEmporium"
            ],
            "Tech Reviews": [
                "MarquesBrownlee", "UnboxTherapy", "LinusTechTips",
                "TheVerge", "MrWhosTheBoss", "iJustine",
                "TechLinked", "ShortCircuit", "JerryRigEverything"
            ],
            "Programming": [
                "Fireship", "TraversyMedia", "TheNetNinja",
                "WebDevSimplified", "freeCodeCamp", "CodingGarden",
                "CodingTech", "KevinPowell", "BenAwad"
            ],
            "Finance & Business": [
                "GrahamStephan", "AndreJikh", "AliAbdaal",
                "TheSwedishInvestor", "TomBilyeu", "PatrickBoyleOnFinance",
                "BeatTheBush", "TwoSidedMedia", "FinancialEducation"
            ],
            "Health & Fitness": [
                "AthleanX", "JeffNippard", "WheezyWaiter",
                "HealthyGamerGG", "PictureFit", "JeremyEthier",
                "BuffDudes", "Blogilates", "FitnessBlender"
            ]
        }

        # Create tabs for categories
        category_tabs = st.tabs(list(categories.keys()))

        for i, (category, channels) in enumerate(categories.items()):
            with category_tabs[i]:
                # Display channels in grid layout with 3 columns
                cols = st.columns(3)
                for j, channel in enumerate(channels):
                    with cols[j % 3]:
                        if st.button(channel, key=f"popular_{category}_{j}"):
                            select_popular_channel(channel)

    with favorites_tab:
        st.markdown('<div class="section-header">Favorite Channels</div>', unsafe_allow_html=True)

        # Load favorites from session state or initialize
        if 'favorites' not in st.session_state:
            st.session_state.favorites = []

        # Show message if no favorites
        if not st.session_state.favorites:
            st.info("You haven't added any favorites yet. Search for a channel and click 'Add to Favorites' to see it here.")
        else:
            # Display favorites in a grid layout
            cols = st.columns(3)
            for i, channel in enumerate(st.session_state.favorites):
                with cols[i % 3]:
                    if st.button(channel, key=f"fav_{i}"):
                        select_favorite_channel(channel)

            # Add button to clear favorites
            if st.button("Clear All Favorites"):
                st.session_state.favorites = []
                st.rerun()

    # Display channel info and videos if available
    if st.session_state.channel_info and st.session_state.videos:
        channel = st.session_state.channel_info

        # Create a card for the channel info
        st.markdown('<div class="card">', unsafe_allow_html=True)

        # Channel header with title and subscriber count
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.subheader(channel['title'])
            st.markdown(f"[View on YouTube](https://www.youtube.com/channel/{channel['id']})")

        with col2:
            if 'subscriber_count' in channel and channel['subscriber_count']:
                st.metric("Subscribers", format_subscribers(channel['subscriber_count']))

        with col3:
            st.metric("Videos Found", len(st.session_state.videos))

            # Add to favorites button
            if 'favorites' not in st.session_state:
                st.session_state.favorites = []

            if channel['title'] in st.session_state.favorites:
                if st.button("❤️ In Favorites"):
                    st.session_state.favorites.remove(channel['title'])
                    st.success(f"Removed {channel['title']} from favorites")
                    st.rerun()
            else:
                if st.button("🤍 Add to Favorites"):
                    st.session_state.favorites.append(channel['title'])
                    st.success(f"Added {channel['title']} to favorites")
                    st.rerun()

        # Channel description
        if 'description' in channel and channel['description']:
            with st.expander("Channel Description"):
                st.markdown(channel['description'])

        st.markdown('</div>', unsafe_allow_html=True)

        # Video browser
        st.markdown('<div class="section-header">Browse & Select Videos</div>', unsafe_allow_html=True)

        # Create dataframe for videos
        videos = st.session_state.videos

        # Extract data for dataframe
        data = []
        for v in videos:
            row = {
                'Title': v['title'],
                'Published': v.get('published_at', 'Unknown'),
                'Duration': format_duration(v['duration_seconds']),
                'Views': f"{int(v['view_count']):,}",
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Create filters for the videos
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            min_duration = st.slider("Min Duration (minutes)", 0, 360, 0)

        with col2:
            max_duration = st.slider("Max Duration (minutes)", 0, 360, 360)

        with col3:
            sort_by = st.selectbox("Sort by", ["Most Recent", "Most Viewed", "Longest", "Shortest"])

        with col4:
            search_text = st.text_input("Search in titles", "")

        # Filter videos
        st.session_state.filtered_videos = list(range(len(videos)))

        # Apply duration filter
        min_seconds = min_duration * 60
        max_seconds = max_duration * 60

        st.session_state.filtered_videos = [i for i in st.session_state.filtered_videos
                                         if min_seconds <= videos[i]['duration_seconds'] <= max_seconds]

        # Apply text search filter
        if search_text:
            search_text = search_text.lower()
            st.session_state.filtered_videos = [i for i in st.session_state.filtered_videos if search_text in videos[i]['title'].lower()]

        # Apply sorting
        if sort_by == "Most Recent":
            # Sort by published date if available
            if 'published_at' in videos[0]:
                st.session_state.filtered_videos.sort(key=lambda i: videos[i].get('published_at', ''), reverse=True)
        elif sort_by == "Most Viewed":
            st.session_state.filtered_videos.sort(key=lambda i: int(videos[i]['view_count']), reverse=True)
        elif sort_by == "Longest":
            st.session_state.filtered_videos.sort(key=lambda i: videos[i]['duration_seconds'], reverse=True)
        elif sort_by == "Shortest":
            st.session_state.filtered_videos.sort(key=lambda i: videos[i]['duration_seconds'])

        # Update the dataframe with the filtered videos
        if st.session_state.filtered_videos:
            filtered_df = df.iloc[st.session_state.filtered_videos].reset_index(drop=True)
        else:
            filtered_df = pd.DataFrame(columns=df.columns)
            st.warning("No videos match your filters. Try adjusting your criteria.")

        # Create multiselect with video titles
        options = st.session_state.filtered_videos
        labels = [f"{videos[i]['title']} ({format_duration(videos[i]['duration_seconds'])})"
                 for i in st.session_state.filtered_videos]

        # Multiselect for video selection
        st.multiselect(
            label="Select videos to analyze:",
            options=options,
            format_func=lambda x: labels[x] if x < len(labels) else "",
            key="video_selection"
        )

        # Add CSS for better button alignment
        st.markdown("""
        <style>
        .analysis-buttons-container {
            display: flex;
            justify-content: space-between;
            gap: 15px;
            margin: 20px 0;
        }
        .analysis-button {
            flex: 1;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)

        # Get number of selected videos
        num_selected = len(st.session_state.get('video_selection', []))

        # Start container for buttons
        st.markdown('<div class="analysis-buttons-container">', unsafe_allow_html=True)

        # View details button
        st.markdown('<div class="analysis-button">', unsafe_allow_html=True)
        view_details = st.button("🎬 View Selected Video Details", key="view_details_button")
        st.markdown('</div>', unsafe_allow_html=True)

        # Analyze button
        st.markdown('<div class="analysis-button">', unsafe_allow_html=True)
        if num_selected > 0:
            analyze_button = st.button(f"Analyze {num_selected} Selected Videos", key="analyze_button")
        else:
            analyze_button = st.button("Analyze Selected Videos", key="analyze_button")
        st.markdown('</div>', unsafe_allow_html=True)

        # Clear selection button
        st.markdown('<div class="analysis-button">', unsafe_allow_html=True)
        if num_selected > 0:
            clear_button = st.button("Clear Selection", key="clear_button")
        else:
            # Empty placeholder to maintain layout
            st.write("")
        st.markdown('</div>', unsafe_allow_html=True)

        # Show how many videos are selected
        if st.session_state.filtered_videos:
            st.caption(f"Showing {len(st.session_state.filtered_videos)} videos. {num_selected} selected for analysis.")
        else:
            st.caption(f"No videos match the current filters.")

        # Handle button actions
        if analyze_button:
            analyze_selected_videos()

        if 'clear_button' in locals() and clear_button:
            st.session_state.video_selection = []
            st.rerun()

        if view_details:
            # Only show details if exactly one video is selected
            if num_selected == 1:
                # Get the selected video
                selected_index = st.session_state.video_selection[0]
                actual_index = st.session_state.filtered_videos[selected_index]
                video = videos[actual_index]

                # Initialize session state for pre-analysis video details if not exists
                if 'show_pre_analysis_details' not in st.session_state:
                    st.session_state.show_pre_analysis_details = None

                # Toggle display
                if st.session_state.show_pre_analysis_details == video['id']:
                    st.session_state.show_pre_analysis_details = None
                else:
                    st.session_state.show_pre_analysis_details = video['id']

                st.rerun()
            else:
                st.warning("Please select exactly one video to view details.")

        # Display table of videos
        st.dataframe(filtered_df, use_container_width=True, height=300)

        # Show video details if a single video is selected
        if 'show_pre_analysis_details' in st.session_state and st.session_state.show_pre_analysis_details:
            video_id = st.session_state.show_pre_analysis_details
            video_data = None

            # Find the video in the list
            for video in videos:
                if video['id'] == video_id:
                    video_data = video
                    break

            if video_data:
                st.markdown("### Video Details")

                # Add a close button
                if st.button("✖️ Close", key="close_pre_analysis"):
                    st.session_state.show_pre_analysis_details = None
                    st.rerun()

                # Create a card for the video details
                st.markdown('<div class="card">', unsafe_allow_html=True)

                col1, col2 = st.columns([2, 3])

                with col1:
                    # Video thumbnail
                    thumbnail_url = f"https://img.youtube.com/vi/{video_data['id']}/hqdefault.jpg"
                    st.image(thumbnail_url, use_column_width=True)

                    # Video stats
                    st.markdown(f"**Duration:** {format_duration(video_data['duration_seconds'])}")
                    st.markdown(f"**Views:** {int(video_data['view_count']):,}")

                    # Link to watch on YouTube
                    st.markdown(f"[Watch on YouTube](https://www.youtube.com/watch?v={video_data['id']})")

                with col2:
                    # Video title and description
                    st.markdown(f"## {video_data['title']}")

                    if 'published_at' in video_data and video_data['published_at']:
                        # Format date
                        pub_date = datetime.fromisoformat(video_data['published_at'].replace('Z', '+00:00'))
                        st.markdown(f"Published on: {pub_date.strftime('%b %d, %Y')}")

                    if 'description' in video_data and video_data['description']:
                        st.markdown("### Description")
                        st.markdown(video_data['description'])

                st.markdown('</div>', unsafe_allow_html=True)

    # Display analysis results if available
    if st.session_state.analyzed_videos:
        st.markdown('<div class="section-header">Analysis Results</div>', unsafe_allow_html=True)

        if not st.session_state.analyzed_videos:
            st.info("No videos have been analyzed yet. Select some videos above and click 'Analyze Selected Videos' to get started.")
        else:
            # Create tabs for each analyzed video with fallback for title key
            videos_tabs = st.tabs([f"{video.get('video_title', video.get('title', 'Unknown Video'))}" for video in st.session_state.analyzed_videos])

            for i, tab in enumerate(videos_tabs):
                with tab:
                    video_report = st.session_state.analyzed_videos[i]
                    # Ensure video report has consistent keys
                    if 'video_title' not in video_report and 'title' in video_report:
                        video_report['video_title'] = video_report['title']

                    # Display the video report
                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Summary", "Key Points", "Topics", "Important Facts", "Technical Details", "Examples & Segments"])

                    with tab1:
                        # Summary tab
                        # Handle both direct fields and nested fields under 'analysis'
                        summary = video_report.get('summary')
                        if not summary and 'analysis' in video_report:
                            summary = video_report['analysis'].get('summary') or video_report['analysis'].get('overall_summary')
                        if summary:
                            st.markdown(summary)
                        else:
                            st.info("No summary available for this video.")

                    with tab2:
                        # Key Points tab
                        points = video_report.get('key_points')
                        if not points and 'analysis' in video_report:
                            points = video_report['analysis'].get('key_points')

                        if points:
                            # Check if it's a list or string
                            if isinstance(points, list):
                                for point in points:
                                    st.markdown(f"• {point}")
                            else:
                                st.markdown(points)
                        else:
                            st.info("No key points available for this video.")

                    with tab3:
                        # Topics tab
                        topics = video_report.get('topics') or video_report.get('main_topics')
                        if not topics and 'analysis' in video_report:
                            topics = video_report['analysis'].get('topics') or video_report['analysis'].get('main_topics')

                        if topics:
                            # Check if it's a list or string
                            if isinstance(topics, list):
                                for topic in topics:
                                    st.markdown(f"• {topic}")
                            else:
                                st.markdown(topics)
                        else:
                            st.info("No topics available for this video.")

                    with tab4:
                        # Important Facts tab
                        facts = video_report.get('important_facts')
                        if not facts and 'analysis' in video_report:
                            facts = video_report['analysis'].get('important_facts')

                        if facts:
                            # Check if it's a list or string
                            if isinstance(facts, list):
                                for fact in facts:
                                    st.markdown(f"• {fact}")
                            else:
                                st.markdown(facts)
                        else:
                            st.info("No important facts available for this video.")

                    with tab5:
                        # Technical Details tab
                        details = video_report.get('technical_details') or video_report.get('technologies_mentioned')
                        if not details and 'analysis' in video_report:
                            details = video_report['analysis'].get('technical_details') or video_report['analysis'].get('technologies_mentioned')

                        if details:
                            # Check if it's a list or string
                            if isinstance(details, list):
                                for detail in details:
                                    st.markdown(f"• {detail}")
                            else:
                                st.markdown(details)
                        else:
                            st.info("No technical details available for this video.")

                    with tab6:
                        # Examples & Segments tab
                        # First try to get from analysis dict, then fallback to top-level
                        examples = None
                        if 'analysis' in video_report:
                            examples = (video_report['analysis'].get('examples_and_segments') or
                                      video_report['analysis'].get('examples_and_stories') or
                                      video_report['analysis'].get('important_segments'))

                        # If not found in analysis dict, try top-level fields
                        if not examples:
                            examples = (video_report.get('examples_and_segments') or
                                      video_report.get('examples_and_stories') or
                                      video_report.get('important_segments'))

                        if examples:
                            # Check if it's a list or string
                            if isinstance(examples, list):
                                for example in examples:
                                    st.markdown(f"• {example}")
                            else:
                                st.markdown(examples)
                        else:
                            st.info("No examples or segments available for this video.")

                    # Add a link to go to the Q&A page
                    st.markdown("---")
                    st.markdown("Have questions about this video? Go to the Q&A page to ask specific questions.")

# Run the app
display_analyze_page()
