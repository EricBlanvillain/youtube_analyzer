#!/usr/bin/env python3
"""
Streamlit web interface for YouTube Analyzer.
This app provides a user-friendly interface to analyze YouTube videos and
ask questions about analyzed content.
"""
import os
import streamlit as st
import pandas as pd
from datetime import datetime
import time
import base64
import json
import ssl

from src.orchestrator import WorkflowOrchestrator
from src.vector_store import VectorStore
from utils.config import config

# Set page configuration
st.set_page_config(
    page_title="YouTube Analyzer",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
def local_css():
    st.markdown("""
    <style>
        /* General theme */
        .stApp {
            background-color: #121212;
            color: #f0f0f0;
        }

        /* Main title */
        .main-title {
            color: #FF0000;
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            margin-bottom: 0 !important;
            text-align: center;
        }

        /* Subtitle */
        .subtitle {
            color: #e0e0e0;
            font-size: 1rem !important;
            text-align: center;
            margin-bottom: 2rem;
            opacity: 0.8;
        }

        /* Card styling */
        .card {
            border-radius: 8px;
            padding: 20px;
            background-color: #1e1e1e;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
            margin-bottom: 20px;
            border-left: 3px solid #FF0000;
        }

        /* Buttons */
        .stButton>button {
            background-color: #FF0000;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.4rem 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .stButton>button:hover {
            background-color: #CC0000;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        /* Section headers */
        .section-header {
            font-size: 1.3rem;
            font-weight: 500;
            color: #f0f0f0;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid #FF0000;
            padding-bottom: 0.3rem;
            opacity: 0.9;
        }

        /* Sidebar */
        .css-1d391kg, [data-testid="stSidebar"] {
            background-color: #1a1a1a;
        }

        /* Inputs */
        .stTextInput>div>div>input {
            background-color: #2d2d2d;
            color: #f0f0f0;
            border: 1px solid #444;
        }

        .stTextArea>div>div>textarea {
            background-color: #2d2d2d;
            color: #f0f0f0;
            border: 1px solid #444;
        }

        /* Search interface styling */
        .search-container {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 1rem;
        }

        .search-button {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            display: flex;
            align-items: flex-start;
            height: 38px;
            position: relative;
        }

        /* Make input and button heights consistent */
        .stButton button {
            height: 38px;
            padding-top: 0;
            padding-bottom: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            top: -2px;
        }

        /* Metrics */
        [data-testid="stMetric"] {
            background-color: #2d2d2d;
            padding: 10px;
            border-radius: 5px;
            border-left: 2px solid #FF0000;
        }

        [data-testid="stMetricLabel"] {
            color: #bbbbbb !important;
        }

        [data-testid="stMetricValue"] {
            color: #ffffff !important;
        }

        /* Dataframe */
        .stDataFrame {
            background-color: #2d2d2d;
        }

        /* Expander */
        .streamlit-expanderHeader {
            background-color: #2d2d2d;
            color: #f0f0f0 !important;
            border-radius: 4px;
        }

        .streamlit-expanderContent {
            background-color: #252525;
            color: #f0f0f0;
            border-radius: 0 0 4px 4px;
        }

        /* Hide hamburger menu and footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Spacing and headers */
        h1, h2, h3 {
            color: #f0f0f0;
        }

        /* Progress bar */
        .stProgress > div > div > div > div {
            background-color: #FF0000;
        }
    </style>
    """, unsafe_allow_html=True)

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
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'showing_video_details' not in st.session_state:
    st.session_state.showing_video_details = None
if 'show_pre_analysis_details' not in st.session_state:
    st.session_state.show_pre_analysis_details = None
if 'digest' not in st.session_state:
    st.session_state.digest = None
if 'digest_channels' not in st.session_state:
    st.session_state.digest_channels = []
if 'digest_processing' not in st.session_state:
    st.session_state.digest_processing = False

def check_api_keys():
    """Check if required API keys are set."""
    missing_keys = []
    if not config.youtube_api_key:
        missing_keys.append("YouTube API Key")
    if not config.anthropic_api_key:
        missing_keys.append("Anthropic API Key")

    if missing_keys:
        st.error(f"Missing required API keys: {', '.join(missing_keys)}")
        st.info("Please add these keys to your .env file and restart the application.")
        return False
    return True

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

def ask_question():
    """Ask a question about analyzed videos."""
    question = st.session_state.question

    if not question:
        st.error("Please enter a question.")
        return

    if not st.session_state.reports:
        st.error("No analyzed videos available. Please analyze some videos first.")
        return

    # Get selected videos for the question
    video_ids = None
    if st.session_state.get('specific_videos', False):
        video_selections = st.session_state.get('qa_video_selection', [])
        if video_selections:
            video_ids = [st.session_state.reports[i]['video_id'] for i in video_selections]

    # Ask the question
    with st.spinner("Analyzing your question..."):
        answer = st.session_state.orchestrator.ask_question(question, video_ids)

    # Store answer in session state
    st.session_state.answer = answer

def get_app_header():
    """Return the HTML for the app header."""
    return """
    <div style="display: flex; justify-content: center; align-items: center; padding: 1rem 0; background: linear-gradient(90deg, #0f0f0f 0%, #202020 100%); margin-bottom: 20px;">
        <div style="display: flex; align-items: center; margin-right: 1rem;">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="36" height="36" fill="#FF0000">
                <path d="M23.495 6.205a3.007 3.007 0 0 0-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 0 0 .527 6.205a31.247 31.247 0 0 0-.522 5.805 31.247 31.247 0 0 0 .522 5.783 3.007 3.007 0 0 0 2.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 0 0 2.088-2.088 31.247 31.247 0 0 0 .5-5.783 31.247 31.247 0 0 0-.5-5.805zM9.609 15.601V8.408l6.264 3.602z"/>
            </svg>
        </div>
        <div>
            <h1 style="color: white; margin: 0; font-size: 1.8rem; font-weight: 600;">YouTube Analyzer</h1>
            <p style="color: #aaaaaa; margin: 0; font-size: 0.9rem;">Powered by AI & YouTube Data API</p>
        </div>
    </div>
    """

def display_analyze_page():
    """Display the video analysis page."""
    st.markdown('<div class="section-header">Analyze YouTube Videos</div>', unsafe_allow_html=True)

    # Channel search section
    st.markdown('<div class="card">', unsafe_allow_html=True)

    # Create tabs for searching and selecting from popular channels
    search_tab, popular_tab, favorites_tab = st.tabs(["Search by Name", "Browse Popular Channels", "My Favorites"])

    with search_tab:
        st.markdown("#### Enter a YouTube channel name")

        # Use a form for better control of layout
        with st.form(key="search_form", clear_on_submit=False):
            # Use columns with a better ratio for alignment
            search_col1, search_col2 = st.columns([6, 1])

            with search_col1:
                st.text_input(
                    label="Channel name",
                    key="channel_name",
                    placeholder="e.g., Huberman Lab",
                    label_visibility="collapsed"
                )

            with search_col2:
                submit_button = st.form_submit_button(
                    label="Search",
                    use_container_width=True
                )

        # Handle form submission
        if submit_button:
            search_channel()

        # Recent searches section (if any)
        if 'recent_searches' not in st.session_state:
            st.session_state.recent_searches = []

        if st.session_state.recent_searches:
            st.markdown("#### Recent Searches")
            recent_cols = st.columns(min(4, len(st.session_state.recent_searches)))
            for i, recent in enumerate(st.session_state.recent_searches[-4:]):  # Show last 4 searches
                with recent_cols[i % 4]:
                    if st.button(f"{recent}", key=f"recent_{i}"):
                        st.session_state.channel_name = recent
                        search_channel()

    with popular_tab:
        # Define categories and channels
        channel_categories = {
            "Health & Wellness": [
                {"name": "Huberman Lab", "subscribers": "6.67M", "description": "Neuroscience-backed wellness & performance insights"},
                {"name": "Doctor Mike", "subscribers": "13.3M", "description": "Evidence-based medical advice from a physician"},
                {"name": "Dr. Eric Berg DC", "subscribers": "13.0M", "description": "Nutrition & hormonal health deep dives"}
            ],
            "Fitness": [
                {"name": "Jeff Nippard", "subscribers": "6.7M", "description": "Science-driven strength training & physique programming"},
                {"name": "ATHLEAN-X", "subscribers": "14.0M", "description": "Biomechanics-based workout tutorials by a physical therapist"},
                {"name": "Jeremy Ethier", "subscribers": "7.08M", "description": "Evidence-based exercise form & nutrition breakdowns"},
                {"name": "Chloe Ting", "subscribers": "25.5M", "description": "Viral at-home workouts & fitness challenges"},
                {"name": "MadFit", "subscribers": "10.0M", "description": "Dance-inspired & bodyweight workout routines"}
            ],
            "Technology": [
                {"name": "Linus Tech Tips", "subscribers": "16.3M", "description": "Consumer-tech reviews, PC builds & gadget deep dives"},
                {"name": "Marques Brownlee", "subscribers": "19.8M", "description": "High-production tech reviews & interviews"},
                {"name": "Unbox Therapy", "subscribers": "24.8M", "description": "Entertaining unboxings & gadget tests"}
            ],
            "AI & Machine Learning": [
                {"name": "Two Minute Papers", "subscribers": "1.62M", "description": "Bite-sized explainers of cutting-edge AI research"},
                {"name": "AI Explained", "subscribers": "960K", "description": "In-depth explanations of AI concepts and advancements"},
                {"name": "Yannic Kilcher", "subscribers": "356K", "description": "Technical AI research breakdowns and paper reviews"},
                {"name": "AssemblyAI", "subscribers": "121K", "description": "AI speech tech and LLM deep dives"},
                {"name": "Matt Wolfe", "subscribers": "726K", "description": "AI news, tool demos & tutorials"},
                {"name": "Lex Fridman", "subscribers": "4.66M", "description": "Long-form AI & tech interviews with thought leaders"}
            ],
            "Programming": [
                {"name": "CodeEmporium", "subscribers": "323K", "description": "ML implementation tutorials and AI concepts"},
                {"name": "sentdex", "subscribers": "1.4M", "description": "Practical AI & Python programming tutorials"},
                {"name": "Fireship", "subscribers": "2.4M", "description": "Short, high-intensity coding tutorials"},
                {"name": "freeCodeCamp", "subscribers": "7.8M", "description": "In-depth programming courses and tutorials"},
                {"name": "Traversy Media", "subscribers": "2.3M", "description": "Web development projects and tutorials"}
            ],
            "Science & Education": [
                {"name": "Kurzgesagt", "subscribers": "22.1M", "description": "Animated deep dives into complex science topics"},
                {"name": "Veritasium", "subscribers": "17.5M", "description": "Physics & science communication with engaging experiments"},
                {"name": "Vsauce", "subscribers": "23.9M", "description": "Wide-ranging scientific & philosophical explorations"},
                {"name": "CrashCourse", "subscribers": "16.3M", "description": "Fast-paced, curriculum-style educational series"},
                {"name": "SciShow", "subscribers": "8.15M", "description": "Science news & myth-busting videos"}
            ],
            "French Content": [
                {"name": "Sans Permission", "subscribers": "244K", "description": "In-depth interviews & conversations in French"},
                {"name": "HugoDécrypte", "subscribers": "3.27M", "description": "Daily news analysis aimed at young French speakers"},
                {"name": "Hugo Tout Seul", "subscribers": "2.17M", "description": "Humorous French commentary & sketches"},
                {"name": "Nota Bene", "subscribers": "1.2M", "description": "French history and culture documentaries"},
                {"name": "Poisson Fécond", "subscribers": "1.8M", "description": "Science vulgarization in French"},
                {"name": "Cyrus North", "subscribers": "834K", "description": "Philosophy and ideas in accessible French"},
                {"name": "Doc Seven", "subscribers": "2.95M", "description": "French documentary-style educational content"},
                {"name": "DirtyBiology", "subscribers": "1.48M", "description": "French biology and science explanations"},
                {"name": "Scilabus", "subscribers": "520K", "description": "French science experiments and explanations"}
            ],
            "French Tech & AI": [
                {"name": "Micode", "subscribers": "1.28M", "description": "French tech, hacking and cybersecurity content"},
                {"name": "Léo Duff", "subscribers": "498K", "description": "French AI news and technology analysis"},
                {"name": "Monsieur IA", "subscribers": "38.5K", "description": "French AI tutorials and explanations"},
                {"name": "Underscore_", "subscribers": "372K", "description": "French programming and tech tutorials"},
                {"name": "Graven - Développement", "subscribers": "481K", "description": "French coding tutorials and projects"},
                {"name": "Xolam", "subscribers": "59.4K", "description": "French AI and machine learning concepts"}
            ]
        }

        # Create a selectbox for categories
        selected_category = st.selectbox(
            label="Select a category",
            options=list(channel_categories.keys()),
            index=0
        )

        # Display channels in the selected category
        if selected_category:
            st.subheader(f"{selected_category} Channels")

            for i, channel in enumerate(channel_categories[selected_category]):
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**{channel['name']}** • {channel['description']}")

                with col2:
                    st.markdown(f"<div style='text-align: right;'>{channel['subscribers']} subscribers</div>", unsafe_allow_html=True)

                with col3:
                    col3a, col3b = st.columns([1, 1])
                    with col3a:
                        if st.button(f"Select", key=f"select_{selected_category}_{i}"):
                            # Use the callback function instead of directly setting session state
                            select_popular_channel(channel['name'])
                    with col3b:
                        # Add a star button to add/remove from favorites
                        # Initialize favorites in session state if not exists
                        if 'favorite_channels' not in st.session_state:
                            st.session_state.favorite_channels = []

                        is_favorite = channel['name'] in st.session_state.favorite_channels
                        button_label = "⭐" if is_favorite else "☆"

                        if st.button(button_label, key=f"fav_{selected_category}_{i}"):
                            if is_favorite:
                                st.session_state.favorite_channels.remove(channel['name'])
                            else:
                                st.session_state.favorite_channels.append(channel['name'])
                            st.rerun()

    # Add favorites tab content
    with favorites_tab:
        if 'favorite_channels' not in st.session_state:
            st.session_state.favorite_channels = []

        if not st.session_state.favorite_channels:
            st.info("You haven't added any favorite channels yet. Browse popular channels and click the star icon to add them here.")
        else:
            st.subheader("Your Favorite Channels")

            for i, channel_name in enumerate(st.session_state.favorite_channels):
                # Find the channel in our categories to get the info
                channel_info = None
                for category in channel_categories.values():
                    for ch in category:
                        if ch['name'] == channel_name:
                            channel_info = ch
                            break
                    if channel_info:
                        break

                # If we found the channel info, display it
                if channel_info:
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.markdown(f"**{channel_info['name']}** • {channel_info['description']}")

                    with col2:
                        st.markdown(f"<div style='text-align: right;'>{channel_info['subscribers']} subscribers</div>", unsafe_allow_html=True)

                    with col3:
                        col3a, col3b = st.columns([1, 1])
                        with col3a:
                            if st.button(f"Select", key=f"select_fav_{i}"):
                                # Use the callback function instead of directly setting session state
                                select_favorite_channel(channel_name)
                        with col3b:
                            if st.button("⭐", key=f"remove_fav_{i}"):
                                st.session_state.favorite_channels.remove(channel_name)
                                st.rerun()
                else:
                    # If we don't have the channel info, just show the name
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(f"**{channel_name}**")
                    with col2:
                        col2a, col2b = st.columns([1, 1])
                        with col2a:
                            if st.button(f"Select", key=f"select_fav_{i}"):
                                # Use the callback function instead of directly setting session state
                                select_favorite_channel(channel_name)
                        with col2b:
                            if st.button("⭐", key=f"remove_fav_{i}"):
                                st.session_state.favorite_channels.remove(channel_name)
                                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Display channel info
    if st.session_state.channel_info:
        channel = st.session_state.channel_info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Channel", channel['title'])
        with col2:
            st.metric("Subscribers", format_subscribers(channel['subscriber_count']))
        with col3:
            st.metric("Videos", channel['video_count'])

    # Display videos
    if st.session_state.videos:
        st.markdown('<div class="section-header">Select Videos to Analyze</div>', unsafe_allow_html=True)

        # Create a dataframe for the videos
        video_data = []
        for i, video in enumerate(st.session_state.videos):
            video_data.append({
                "Title": video['title'],
                "Duration": format_duration(video['duration_seconds']),
                "Views": int(video['view_count']),
                "Date": video.get('published_at', '').split('T')[0] if 'published_at' in video else '',
            })

        df = pd.DataFrame(video_data)

        # Add filter options for videos
        filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 1])

        with filter_col1:
            # Duration filter
            duration_options = ["All", "Short (<5min)", "Medium (5-20min)", "Long (>20min)"]
            duration_filter = st.selectbox(
                label="Duration Filter",
                options=duration_options,
                index=0
            )

        with filter_col2:
            # Text search
            search_text = st.text_input(
                label="Search in titles",
                placeholder="Enter keywords",
                key="video_search"
            )

        with filter_col3:
            # Sort options
            sort_options = ["Most Recent", "Most Viewed", "Longest", "Shortest"]
            sort_by = st.selectbox(
                label="Sort By",
                options=sort_options,
                index=0
            )

        # Apply filters to the list of videos
        st.session_state.filtered_videos = list(range(len(st.session_state.videos)))

        # Filter by duration
        if duration_filter != "All":
            if duration_filter == "Short (<5min)":
                st.session_state.filtered_videos = [i for i in st.session_state.filtered_videos if st.session_state.videos[i]['duration_seconds'] < 300]
            elif duration_filter == "Medium (5-20min)":
                st.session_state.filtered_videos = [i for i in st.session_state.filtered_videos if 300 <= st.session_state.videos[i]['duration_seconds'] <= 1200]
            elif duration_filter == "Long (>20min)":
                st.session_state.filtered_videos = [i for i in st.session_state.filtered_videos if st.session_state.videos[i]['duration_seconds'] > 1200]

        # Filter by search text
        if search_text:
            search_text = search_text.lower()
            st.session_state.filtered_videos = [i for i in st.session_state.filtered_videos if search_text in st.session_state.videos[i]['title'].lower()]

        # Apply sorting
        if sort_by == "Most Recent":
            # Sort by published date if available
            if 'published_at' in st.session_state.videos[0]:
                st.session_state.filtered_videos.sort(key=lambda i: st.session_state.videos[i].get('published_at', ''), reverse=True)
        elif sort_by == "Most Viewed":
            st.session_state.filtered_videos.sort(key=lambda i: int(st.session_state.videos[i]['view_count']), reverse=True)
        elif sort_by == "Longest":
            st.session_state.filtered_videos.sort(key=lambda i: st.session_state.videos[i]['duration_seconds'], reverse=True)
        elif sort_by == "Shortest":
            st.session_state.filtered_videos.sort(key=lambda i: st.session_state.videos[i]['duration_seconds'])

        # Update the dataframe with the filtered videos
        if st.session_state.filtered_videos:
            filtered_df = df.iloc[st.session_state.filtered_videos].reset_index(drop=True)
        else:
            filtered_df = pd.DataFrame(columns=df.columns)
            st.warning("No videos match your filters. Try adjusting your criteria.")

        # Create multiselect with video titles
        options = st.session_state.filtered_videos
        labels = [f"{st.session_state.videos[i]['title']} ({format_duration(st.session_state.videos[i]['duration_seconds'])})"
                 for i in st.session_state.filtered_videos]

        # Multiselect for video selection
        st.multiselect(
            label="Select videos to analyze:",
            options=options,
            format_func=lambda x: labels[x] if x < len(labels) else "",
            key="video_selection"
        )

        # Button to analyze videos
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            num_selected = len(st.session_state.get('video_selection', []))
            if num_selected > 0:
                st.button(f"Analyze {num_selected} Selected Videos", on_click=analyze_selected_videos)
            else:
                st.button("Analyze Selected Videos", on_click=analyze_selected_videos)

            # Show how many videos are selected
            if st.session_state.filtered_videos:
                st.caption(f"Showing {len(st.session_state.filtered_videos)} videos. {num_selected} selected for analysis.")
            else:
                st.caption(f"No videos match the current filters.")

        # Add a clear selection button if videos are selected
        if num_selected > 0:
            with col3:
                if st.button("Clear Selection"):
                    st.session_state.video_selection = []
                    st.rerun()

            # Add a "View Video Details" button
            with col1:
                if st.button("🎬 View Selected Video Details"):
                    # Only show details if exactly one video is selected
                    if num_selected == 1:
                        # Get the selected video
                        selected_index = st.session_state.video_selection[0]
                        actual_index = st.session_state.filtered_videos[selected_index]
                        video = st.session_state.videos[actual_index]

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
            for video in st.session_state.videos:
                if video['id'] == video_id:
                    video_data = video
                    break

            if video_data:
                st.markdown("### Video Details")

                # Add a close button
                if st.button("✖️ Close", key="close_pre_analysis"):
                    st.session_state.show_pre_analysis_details = None
                    st.rerun()

                # Display details in two columns
                col1, col2 = st.columns([1, 2])

                with col1:
                    # Display the video thumbnail
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                    st.image(thumbnail_url, use_column_width=True)

                    # Add a link to the video
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    st.markdown(f"[Watch on YouTube]({video_url})")

                with col2:
                    # Display video statistics
                    st.markdown(f"**Title:** {video_data['title']}")
                    # Try different possible keys for channel name with fallbacks
                    channel_name = video_data.get('channel_title') or video_data.get('channelTitle') or video_data.get('channel_name') or st.session_state.channel_info.get('title', 'Unknown channel') if st.session_state.channel_info else 'Unknown channel'
                    st.markdown(f"**Channel:** {channel_name}")
                    st.markdown(f"**Published:** {video_data.get('published_at', '').split('T')[0] if 'published_at' in video_data else 'Not available'}")
                    st.markdown(f"**Views:** {int(video_data['view_count']):,}")
                    st.markdown(f"**Duration:** {format_duration(video_data['duration_seconds'])}")
                    if 'like_count' in video_data:
                        st.markdown(f"**Likes:** {int(video_data['like_count']):,}")
                    if 'comment_count' in video_data:
                        st.markdown(f"**Comments:** {int(video_data['comment_count']):,}")

                # Display video description
                if 'description' in video_data and video_data['description']:
                    st.markdown("### Description")
                    st.text_area("", value=video_data['description'], height=200, disabled=True, label_visibility="collapsed")

                # Display tags if available
                if 'tags' in video_data and video_data['tags']:
                    st.markdown("### Tags")
                    tags_text = ', '.join(video_data['tags'])
                    st.text_area("", value=tags_text, height=100, disabled=True, label_visibility="collapsed")

    # Display analyzed videos
    if st.session_state.analyzed_videos:
        st.markdown('<div class="section-header">Analysis Results</div>', unsafe_allow_html=True)

        for report in st.session_state.analyzed_videos:
            with st.expander(f"📊 {report['video_title']}"):
                st.markdown(f"**Analyzed:** {report['analysis_timestamp']}")

                # Add "View Video Details" button at the top of the expander
                col_details, col_spacer = st.columns([1, 3])
                with col_details:
                    st.button(
                        f"🎬 View Video Details",
                        key=f"view_details_{report['video_id']}",
                        on_click=toggle_video_details,
                        args=(report['video_id'],)
                    )

                # Show video details if this video is selected
                if st.session_state.showing_video_details == report['video_id']:
                    with st.container():
                        # Add a close button
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown("### Video Details")
                        with col2:
                            st.button("✖️ Close", key=f"close_{report['video_id']}", on_click=toggle_video_details)

                        # Create two columns for thumbnail and stats
                        col1, col2 = st.columns([1, 2])

                        with col1:
                            # Display the video thumbnail
                            thumbnail_url = f"https://img.youtube.com/vi/{report['video_id']}/hqdefault.jpg"
                            st.image(thumbnail_url, use_column_width=True)

                            # Add a link to the video
                            video_url = f"https://www.youtube.com/watch?v={report['video_id']}"
                            st.markdown(f"[Watch on YouTube]({video_url})")

                        with col2:
                            # Display video statistics
                            video_data = None
                            for video in st.session_state.videos:
                                if video['id'] == report['video_id']:
                                    video_data = video
                                    break

                            if video_data:
                                st.markdown(f"**Title:** {video_data['title']}")
                                # Try different possible keys for channel name with fallbacks
                                channel_name = video_data.get('channel_title') or video_data.get('channelTitle') or video_data.get('channel_name') or st.session_state.channel_info.get('title', 'Unknown channel') if st.session_state.channel_info else 'Unknown channel'
                                st.markdown(f"**Channel:** {channel_name}")
                                st.markdown(f"**Published:** {video_data.get('published_at', '').split('T')[0] if 'published_at' in video_data else 'Not available'}")
                                st.markdown(f"**Views:** {int(video_data['view_count']):,}")
                                st.markdown(f"**Duration:** {format_duration(video_data['duration_seconds'])}")
                                if 'like_count' in video_data:
                                    st.markdown(f"**Likes:** {int(video_data['like_count']):,}")
                                if 'comment_count' in video_data:
                                    st.markdown(f"**Comments:** {int(video_data['comment_count']):,}")

                        # Add a divider
                        st.markdown("---")

                        # Display video description
                        if video_data and 'description' in video_data and video_data['description']:
                            st.markdown("### Description")
                            st.text_area("", value=video_data['description'], height=200, disabled=True, label_visibility="collapsed")

                        # Display tags if available
                        if video_data and 'tags' in video_data and video_data['tags']:
                            st.markdown("### Tags")
                            tags_text = ', '.join(video_data['tags'])
                            st.text_area("", value=tags_text, height=100, disabled=True, label_visibility="collapsed")

                        # Add a divider before tabs
                        st.markdown("---")

                # Create tabs for the analysis results
                tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Summary", "Key Points", "Topics", "Important Facts", "Technical Details", "Examples & Segments"])

                with tab1:
                    st.markdown("### Overall Summary")
                    st.markdown(report['analysis']['overall_summary'])

                    if 'detailed_summary' in report['analysis']:
                        st.markdown("### Detailed Summary")
                        st.markdown(report['analysis']['detailed_summary'])

                    # Display two columns for additional metadata
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### Tone and Style")
                        st.markdown(report['analysis']['tone_and_style'])
                    with col2:
                        # Display the new fields we added
                        if 'target_audience' in report['analysis']:
                            st.markdown("### Target Audience")
                            st.markdown(report['analysis']['target_audience'])

                        if 'content_quality' in report['analysis']:
                            st.markdown("### Content Quality")
                            st.markdown(report['analysis']['content_quality'])

                with tab2:
                    st.markdown("### Key Points")
                    for i, point in enumerate(report['analysis']['key_points']):
                        st.markdown(f"{i+1}. {point}")

                with tab3:
                    st.markdown("### Main Topics")
                    for topic in report['analysis']['main_topics']:
                        st.markdown(f"- {topic}")

                with tab4:
                    st.markdown("### Important Facts & Statements")
                    if 'important_facts' in report['analysis'] and report['analysis']['important_facts']:
                        for fact in report['analysis']['important_facts']:
                            st.markdown(f"- {fact}")
                    else:
                        st.info("No important facts extracted from this video.")

                with tab5:
                    st.markdown("### Technical Details")
                    if 'technical_details' in report['analysis'] and report['analysis']['technical_details'] and report['analysis']['technical_details'][0] != "No technical details mentioned":
                        for detail in report['analysis']['technical_details']:
                            st.markdown(f"- {detail}")
                    else:
                        st.info("No technical details mentioned in this video.")

                with tab6:
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("### Examples & Stories")
                        if 'examples_and_stories' in report['analysis'] and report['analysis']['examples_and_stories'] and report['analysis']['examples_and_stories'][0] != "No examples or stories mentioned":
                            for example in report['analysis']['examples_and_stories']:
                                st.markdown(f"- {example}")
                        else:
                            st.info("No examples or stories mentioned in this video.")

                    with col2:
                        st.markdown("### Important Segments")
                        if 'important_segments' in report['analysis'] and report['analysis']['important_segments'] and report['analysis']['important_segments'][0] != "No important segments identified":
                            for segment in report['analysis']['important_segments']:
                                st.markdown(f"- {segment}")
                        else:
                            st.info("No specific segments identified in this video.")

def display_qa_page():
    """Display the Q&A page."""
    st.markdown('<div class="section-header">Ask Questions About Analyzed Videos</div>', unsafe_allow_html=True)

    reports = st.session_state.reports
    if not reports:
        # Try to load reports
        reports = st.session_state.orchestrator.qa_agent.list_available_reports()
        st.session_state.reports = reports

    if not reports:
        st.warning("No analyzed videos available. Please analyze some videos first.")
        return

    # Display available videos
    video_data = []
    for report in reports:
        video_data.append({
            "Title": report['video_title'],
            "Analysis Date": report['analysis_timestamp'][:10],  # Just the date part
        })

    df = pd.DataFrame(video_data)
    st.dataframe(df, use_container_width=True, height=150)

    # Question input
    st.markdown('<div class="card">', unsafe_allow_html=True)

    # Help information for users
    with st.expander("📋 Tips for asking specific questions"):
        st.markdown("""
        **Get more detailed answers by asking specific questions!**

        Our system has been enhanced to extract and provide detailed information from videos. You can now ask much more specific questions, such as:

        - "What specific statistics or numbers were mentioned in the video about X?"
        - "Did the speaker recommend any specific tools or resources for X?"
        - "What examples or case studies were used to illustrate X?"
        - "What was the exact quote about X?"
        - "In which part of the video did they discuss X?"
        - "What technical methods were described for achieving X?"
        - "How did the speaker compare X and Y approaches?"

        The more specific your question, the more detailed the answer will be!
        """)

    # Option to specify videos for the question
    st.checkbox(
        label="Limit question to specific videos",
        key="specific_videos"
    )

    if st.session_state.get('specific_videos', False):
        options = list(range(len(reports)))
        labels = [f"{report['video_title']}" for i, report in enumerate(reports)]

        st.multiselect(
            label="Select videos to include:",
            options=options,
            format_func=lambda x: labels[x],
            key="qa_video_selection"
        )

    # Add example questions
    if not 'example_questions' in st.session_state:
        st.session_state.example_questions = [
            "What are the main points discussed in these videos?",
            "What specific tools or resources were recommended?",
            "What examples were used to illustrate the concepts?",
            "What statistics or data were mentioned?",
            "How did the speaker compare different approaches?",
            "What technical methods were described in detail?"
        ]

    # Add example question selection
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("**Try an example:**")
    with col2:
        selected_example = st.selectbox(
            label="Select an example question",
            options=st.session_state.example_questions,
            label_visibility="collapsed"
        )
        if st.button("Use This Example"):
            st.session_state.question = selected_example
            st.rerun()

    st.text_area(
        label="Your question:",
        key="question",
        height=80,
        placeholder="What are the main points discussed in these videos?"
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.button("Ask Question", on_click=ask_question, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Display answer
    if 'answer' in st.session_state and st.session_state.answer:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Answer")
        st.markdown(st.session_state.answer)

        # Add a button to ask a follow-up question
        if st.button("Ask a follow-up question"):
            # Clear the previous question to allow for a new one
            st.session_state.question = ""
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

def display_about_page():
    """Display the about page."""
    st.markdown('<div class="section-header">About YouTube Analyzer</div>', unsafe_allow_html=True)

    # Main info card
    st.markdown('<div class="card">', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; margin-top: 20px;">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="120" height="120" fill="#FF0000">
                <path d="M23.495 6.205a3.007 3.007 0 0 0-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 0 0 .527 6.205a31.247 31.247 0 0 0-.522 5.805 31.247 31.247 0 0 0 .522 5.783 3.007 3.007 0 0 0 2.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 0 0 2.088-2.088 31.247 31.247 0 0 0 .5-5.783 31.247 31.247 0 0 0-.5-5.805zM9.609 15.601V8.408l6.264 3.602z"/>
            </svg>
            <div style="margin-top: 15px; text-align: center; font-size: 0.9rem; color: #aaaaaa;">
                Version 1.0
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        ## YouTube Analyzer

        A powerful AI-driven tool that helps you extract insights, summaries, and key information from YouTube videos. This application combines the YouTube Data API with Anthropic's Claude AI to analyze video transcripts and generate comprehensive reports.

        ### Key Features

        - **Channel Discovery**: Search and browse popular YouTube channels across categories
        - **Video Management**: Filter videos by duration, views, and content
        - **In-depth Analysis**: Generate AI-powered reports with summaries, key points, and topics
        - **Smart Q&A**: Ask specific questions about video content and get accurate answers
        - **Content Organization**: Save favorite channels and keep track of recently analyzed videos
        """)

    st.markdown('</div>', unsafe_allow_html=True)

    # How it works section
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("""
    ## How It Works

    <div style="display: flex; margin-top: 20px; margin-bottom: 20px; flex-wrap: wrap; gap: 20px; justify-content: space-between;">
        <div style="flex: 1; min-width: 200px; background-color: #252525; padding: 20px; border-radius: 8px; border-top: 3px solid #FF0000;">
            <h3 style="font-size: 1.1rem; margin-bottom: 10px;">1. Search & Select</h3>
            <p style="font-size: 0.95rem; color: #cccccc;">Search for YouTube channels or browse popular ones. Filter videos by duration, recency, or views to find the most relevant content.</p>
        </div>
        <div style="flex: 1; min-width: 200px; background-color: #252525; padding: 20px; border-radius: 8px; border-top: 3px solid #FF0000;">
            <h3 style="font-size: 1.1rem; margin-bottom: 10px;">2. Analyze Content</h3>
            <p style="font-size: 0.95rem; color: #cccccc;">The AI analyzes the video transcripts to extract key points, topics, technical details, examples, and important segments.</p>
        </div>
        <div style="flex: 1; min-width: 200px; background-color: #252525; padding: 20px; border-radius: 8px; border-top: 3px solid #FF0000;">
            <h3 style="font-size: 1.1rem; margin-bottom: 10px;">3. Ask Questions</h3>
            <p style="font-size: 0.95rem; color: #cccccc;">Ask specific questions about the analyzed videos and get detailed, accurate answers based on the content.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Use Cases
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("""
    ## Use Cases

    <div style="margin-top: 15px;">
        <div style="margin-bottom: 15px;">
            <h3 style="font-size: 1.1rem; color: #FF0000;">🎓 Learning & Research</h3>
            <p style="font-size: 0.95rem; margin-left: 10px;">Extract key information from educational videos, lectures, and tutorials without watching the entire content.</p>
        </div>

        <div style="margin-bottom: 15px;">
            <h3 style="font-size: 1.1rem; color: #FF0000;">📊 Content Analysis</h3>
            <p style="font-size: 0.95rem; margin-left: 10px;">Analyze multiple videos on a topic to compare ideas, approaches, and recommendations.</p>
        </div>

        <div style="margin-bottom: 15px;">
            <h3 style="font-size: 1.1rem; color: #FF0000;">⏱️ Time Saving</h3>
            <p style="font-size: 0.95rem; margin-left: 10px;">Get the essence of long videos in minutes instead of spending hours watching them.</p>
        </div>

        <div style="margin-bottom: 15px;">
            <h3 style="font-size: 1.1rem; color: #FF0000;">🔍 Deep Insights</h3>
            <p style="font-size: 0.95rem; margin-left: 10px;">Ask specific questions to extract precise information hidden within hours of video content.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Technical info
    with st.expander("Technical Information"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            ### Technologies Used

            - **Frontend**: Streamlit
            - **Backend**: Python
            - **AI Processing**: Anthropic Claude API
            - **Video Data**: YouTube Data API
            - **Transcript Retrieval**: YouTube Transcript API

            ### Data Privacy

            This application does not store video content itself, only the analysis results.
            All processing is done securely via the Anthropic API with proper authentication.
            """)

        with col2:
            st.markdown("""
            ### System Requirements

            - **API Keys Required**:
              - YouTube Data API key
              - Anthropic API key

            ### Credits

            - YouTube Data API for channel and video metadata
            - Anthropic Claude for AI analysis capabilities
            - Streamlit for the web interface
            """)

    # FAQ Section
    with st.expander("Frequently Asked Questions"):
        st.markdown("""
        #### Q: Is this tool free to use?
        The application itself is free, but you need your own API keys for YouTube and Anthropic.

        #### Q: Can it analyze videos in languages other than English?
        Currently, the tool works best with English content. Support for other languages is planned for future updates.

        #### Q: How accurate are the AI-generated summaries?
        The summaries are generated by Claude, one of the most advanced AI models. While they are generally accurate, they may occasionally miss nuance or context.

        #### Q: Can I export the analysis results?
        Not in the current version, but this feature is planned for a future update.

        #### Q: How many videos can I analyze at once?
        You can analyze multiple videos, but be aware that each video analysis consumes API resources.
        """)

    # Disclaimer
    st.markdown("""
    <div style="margin-top: 30px; font-size: 0.8rem; color: #999999; text-align: center;">
        <p>This tool is not affiliated with YouTube or Google. It is an independent application that uses the YouTube API in compliance with its terms of service.</p>
        <p>YouTube is a trademark of Google LLC.</p>
    </div>
    """, unsafe_allow_html=True)

def display_digest_page():
    """Display the multi-channel digest page."""
    st.markdown('<div class="main-title">Multi-Channel Digest</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Analyze multiple channels to generate AI news digests</div>', unsafe_allow_html=True)

    # Check API keys
    if not check_api_keys():
        return

    # Create tabs for different functions
    setup_tab, results_tab, troubleshoot_tab = st.tabs(["Setup Digest", "View Results", "Troubleshooting"])

    with setup_tab:
        st.markdown('<div class="section-header">Configure Your Digest</div>', unsafe_allow_html=True)

        # Input for channels
        st.subheader("Step 1: Enter YouTube Channels")

        # Create a form for channel inputs
        with st.form("channel_form"):
            channels_input = st.text_area(
                "Enter channel names (one per line):",
                placeholder="E.g.:\nTheAIGRID\nMatt Wolfe\nAll about AI",
                height=100
            )

            # Digest configuration options
            st.subheader("Step 2: Configure Digest")
            col1, col2 = st.columns(2)

            with col1:
                digest_type = st.radio("Digest Type:", ["weekly", "monthly"])

            with col2:
                videos_per_channel = st.slider("Videos per channel:", 1, 10, 3)

            # Advanced options
            with st.expander("Advanced Options"):
                use_ssl_workaround = st.checkbox("Enable SSL/TLS workaround", value=True,
                                         help="Use this if you're experiencing SSL connection issues")
                retry_count = st.slider("Maximum retries:", 1, 5, 3,
                                    help="Number of times to retry API calls if they fail")

            # Submit button
            submit_button = st.form_submit_button("Generate Digest")

            if submit_button:
                # Process the input channels
                channel_names = [name.strip() for name in channels_input.split("\n") if name.strip()]

                if not channel_names:
                    st.error("Please enter at least one channel name.")
                else:
                    # Store the channel names and options in session state
                    st.session_state.digest_channels = channel_names
                    st.session_state.digest_processing = True
                    st.session_state.use_ssl_workaround = use_ssl_workaround
                    st.session_state.retry_count = retry_count
                    st.session_state.digest = None  # Reset any existing digest
                    st.rerun()

        # Display some suggested channels
        with st.expander("Suggested AI/Tech YouTube Channels"):
            st.markdown("""
            - **TheAIGRID** - AI news and tutorials
            - **Matt Wolfe** - AI tools and applications
            - **All About AI** - AI explanations and reviews
            - **Yannic Kilcher** - ML research papers explained
            - **Two Minute Papers** - AI research simplified
            - **AI Explained** - Detailed AI concepts
            - **DeepLearningAI** - Andrew Ng's channel
            - **Computerphile** - Computer science topics including AI
            - **sentdex** - Python and AI tutorials
            """)

    with results_tab:
        # Check if we need to process a digest
        if st.session_state.digest_processing and st.session_state.digest_channels:
            st.markdown('<div class="section-header">Processing Digest</div>', unsafe_allow_html=True)

            # Get the channels to process
            channel_names = st.session_state.digest_channels

            # Show progress for channel processing
            st.write(f"Processing {len(channel_names)} channels: {', '.join(channel_names)}")
            progress_bar = st.progress(0)
            status_text = st.empty()
            error_text = st.empty()

            try:
                # Create data retriever
                data_retriever = st.session_state.orchestrator.data_retriever

                # Get videos from multiple channels
                status_text.text("Retrieving channel information and videos...")
                channel_videos = data_retriever.get_multi_channel_videos(
                    channel_names,
                    max_videos_per_channel=videos_per_channel
                )

                # Update progress
                progress_bar.progress(30)
                status_text.text(f"Retrieved information for {len(channel_videos)} channels.")

                if not channel_videos:
                    st.error("Could not retrieve information for any of the specified channels.")
                    st.session_state.digest_processing = False
                    return

                # Get the report generator
                report_generator = st.session_state.orchestrator.report_generator

                # If the ssl workaround is enabled, set it
                if hasattr(st.session_state, 'use_ssl_workaround') and st.session_state.use_ssl_workaround:
                    status_text.text("Enabling SSL/TLS workaround...")
                    import ssl
                    import requests
                    from requests.adapters import HTTPAdapter
                    from requests.packages.urllib3.poolmanager import PoolManager

                    # Create a custom SSL adapter
                    class TlsAdapter(HTTPAdapter):
                        def init_poolmanager(self, connections, maxsize, block=False):
                            ctx = ssl.create_default_context()
                            # Add OP_LEGACY_SERVER_CONNECT flag (workaround for SSL issues)
                            ctx.options |= 0x4
                            self.poolmanager = PoolManager(
                                num_pools=connections,
                                maxsize=maxsize,
                                block=block,
                                ssl_version=ssl.PROTOCOL_TLS,
                                ssl_context=ctx
                            )

                    # Try to patch the anthropic client's session if possible
                    if hasattr(report_generator.anthropic_client, "_client"):
                        session = getattr(report_generator.anthropic_client._client, "_session", None)
                        if session:
                            session.mount('https://', TlsAdapter())
                            status_text.text("SSL/TLS workaround enabled successfully.")

                # Generate the digest
                status_text.text("Generating digest from retrieved videos... (this may take a few minutes)")
                progress_bar.progress(50)

                try:
                    # Extract all videos into a flat list
                    all_videos = []
                    for channel_info, videos in channel_videos:
                        # Add channel info to each video
                        for video in videos:
                            video["channel"] = {
                                "id": channel_info["id"],
                                "name": channel_info["title"]
                            }
                            all_videos.append(video)

                    status_text.text(f"Processing {len(all_videos)} videos from {len(channel_videos)} channels...")
                    progress_bar.progress(50)

                    # Set retry count if available
                    retry_count = st.session_state.get('retry_count', 3)

                    # Show cache info to the user
                    status_text.text("Checking for cached video analyses...")

                    # Try with multiple retries for SSL issues
                    for attempt in range(retry_count):
                        try:
                            # Show a more informative status message
                            if attempt > 0:
                                status_text.text(f"Generating digest from retrieved videos... (Attempt {attempt+1}/{retry_count})")
                            else:
                                status_text.text("Generating digest from retrieved videos... (this may take a few minutes)")

                            digest = report_generator.generate_digest(all_videos, title=f"{digest_type.capitalize()} AI Video Digest")
                            if digest:
                                break
                        except ssl.SSLError as ssl_err:
                            if attempt < retry_count - 1:
                                error_message = f"SSL Error (attempt {attempt+1}/{retry_count}): {str(ssl_err)}"
                                error_text.warning(error_message)
                                status_text.text(f"Retrying in 3 seconds... (attempt {attempt+1}/{retry_count})")
                                time.sleep(3)
                            else:
                                raise  # Re-raise on last attempt
                        except Exception as e:
                            if attempt < retry_count - 1:
                                error_message = f"API Error (attempt {attempt+1}/{retry_count}): {str(e)}"
                                error_text.warning(error_message)
                                status_text.text(f"Retrying in 3 seconds... (attempt {attempt+1}/{retry_count})")
                                time.sleep(3)
                            else:
                                raise  # Re-raise on last attempt

                    # Update progress
                    progress_bar.progress(100)
                    status_text.text("Digest generation complete!")

                    if digest:
                        st.session_state.digest = digest
                    else:
                        st.error("Failed to generate digest. Please check the logs for more information.")

                except Exception as api_error:
                    error_message = str(api_error)
                    if "SSL" in error_message or "ssl" in error_message:
                        st.error(f"SSL/TLS connection error: {error_message}")
                        st.error("This is usually caused by network security settings or outdated certificates.")
                        st.info("Please try the following:")
                        st.info("1. Check the 'Enable SSL/TLS workaround' option in Advanced Options")
                        st.info("2. Run the test_anthropic.py script for detailed diagnostics")
                        st.info("3. Try a different network connection if available")
                    else:
                        st.error(f"Error calling Anthropic API: {error_message}")

                # Reset processing flag
                st.session_state.digest_processing = False

            except Exception as e:
                error_message = str(e)
                if "SSL" in error_message or "ssl" in error_message:
                    st.error(f"SSL/TLS connection error: {error_message}")
                    st.error("This is usually caused by network security settings or outdated certificates.")
                    st.info("Please visit the Troubleshooting tab for steps to resolve this issue.")
                else:
                    st.error(f"An error occurred while generating the digest: {error_message}")
                st.session_state.digest_processing = False
