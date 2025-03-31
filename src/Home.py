#!/usr/bin/env python3
"""
Home page for YouTube Analyzer app.
This is the main entry point for the application that provides an overview and navigation.
"""
import streamlit as st
import os
import base64

from orchestrator import WorkflowOrchestrator
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

        /* Feature card */
        .feature-card {
            border-radius: 8px;
            padding: 15px;
            background-color: #252525;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            border-left: 2px solid #FF0000;
        }

        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(255, 0, 0, 0.2);
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

        /* Metrics */
        [data-testid="stMetric"] {
            background-color: #2d2d2d;
            padding: 10px;
            border-radius: 5px;
            border-left: 2px solid #FF0000;
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

        /* Hero section */
        .hero {
            text-align: center;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }

        /* Navigation cards */
        .nav-card {
            border-radius: 8px;
            padding: 20px;
            background-color: #1e1e1e;
            transition: all 0.3s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
            border-top: 3px solid #FF0000;
        }

        .nav-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(255, 0, 0, 0.2);
        }

        .nav-card h3 {
            color: #FF0000;
            margin-bottom: 10px;
        }

        .nav-card-content {
            flex-grow: 1;
        }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state for orchestrator
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = WorkflowOrchestrator()

# Apply styling
local_css()

# Hero section
st.markdown('<div class="hero">', unsafe_allow_html=True)
st.markdown('<div class="main-title">YouTube Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-powered insights from YouTube videos</div>', unsafe_allow_html=True)

# Check API keys
missing_keys = []
if not config.youtube_api_key:
    missing_keys.append("YouTube API Key")
if not config.anthropic_api_key:
    missing_keys.append("Anthropic API Key")

if missing_keys:
    st.error(f"Missing required API keys: {', '.join(missing_keys)}")
    st.info("Please add these keys to your .env file and restart the application.")

    # Show .env setup instructions
    with st.expander("API Keys Setup Instructions"):
        st.markdown("""
        ### How to Set Up API Keys

        1. Create a `.env` file in the root directory of this project
        2. Add the following lines to the file:
        ```
        YOUTUBE_API_KEY=your_youtube_api_key
        ANTHROPIC_API_KEY=your_anthropic_api_key
        ```
        3. Replace the placeholders with your actual API keys
        4. Restart the application

        #### Getting the API Keys

        - [YouTube API Key](https://developers.google.com/youtube/v3/getting-started) - Sign up for Google Cloud and enable the YouTube Data API
        - [Anthropic API Key](https://console.anthropic.com/) - Sign up for an Anthropic account and generate an API key
        """)
else:
    st.success("API keys are properly configured!")

st.markdown('</div>', unsafe_allow_html=True)

# Main navigation cards
st.markdown('<div class="section-header">Explore Features</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    st.markdown('<h3>📺 Analyze Videos</h3>', unsafe_allow_html=True)
    st.markdown('<div class="nav-card-content">', unsafe_allow_html=True)
    st.markdown("""
    Search for YouTube channels, browse videos, and get AI-powered analysis with key points, topics, and important facts.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("Go to Analyzer", key="goto_analyze"):
        st.switch_page("pages/1_Analyze.py")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    st.markdown('<h3>❓ Ask Questions</h3>', unsafe_allow_html=True)
    st.markdown('<div class="nav-card-content">', unsafe_allow_html=True)
    st.markdown("""
    Ask specific questions about analyzed videos and get precise answers powered by AI.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("Go to Q&A", key="goto_qa"):
        st.switch_page("pages/2_Q&A.py")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    st.markdown('<h3>📊 Create Digest</h3>', unsafe_allow_html=True)
    st.markdown('<div class="nav-card-content">', unsafe_allow_html=True)
    st.markdown("""
    Generate summaries and insights from multiple YouTube channels at once.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("Go to Digest", key="goto_digest"):
        st.switch_page("pages/3_Digest.py")
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    st.markdown('<h3>ℹ️ About</h3>', unsafe_allow_html=True)
    st.markdown('<div class="nav-card-content">', unsafe_allow_html=True)
    st.markdown("""
    Learn more about the application, its features, and how to use it effectively.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("Go to About", key="goto_about"):
        st.switch_page("pages/4_About.py")
    st.markdown('</div>', unsafe_allow_html=True)

# Features section
st.markdown('<div class="section-header">Key Features</div>', unsafe_allow_html=True)

features = [
    {
        "icon": "🔍",
        "title": "Channel Discovery",
        "description": "Search for channels or browse popular ones across different categories."
    },
    {
        "icon": "🎥",
        "title": "Video Filtering",
        "description": "Filter videos by duration, views, and content to find what you need."
    },
    {
        "icon": "📝",
        "title": "In-depth Analysis",
        "description": "Get AI-generated summaries, key points, topics, and technical details."
    },
    {
        "icon": "💬",
        "title": "Smart Q&A",
        "description": "Ask questions about video content and receive accurate answers."
    },
    {
        "icon": "📊",
        "title": "Multi-Channel Digest",
        "description": "Generate summaries from multiple channels to track trends and insights."
    },
    {
        "icon": "⏱️",
        "title": "Time Saver",
        "description": "Extract the essence of long videos without watching them entirely."
    }
]

# Display features in a grid
feature_cols = st.columns(3)
for i, feature in enumerate(features):
    with feature_cols[i % 3]:
        st.markdown(f"""
        <div class="feature-card">
            <h3>{feature["icon"]} {feature["title"]}</h3>
            <p>{feature["description"]}</p>
        </div>
        """, unsafe_allow_html=True)

# Getting started section
st.markdown('<div class="section-header">Getting Started</div>', unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("""
### Quick Start Guide

1. Go to the **Analyze** page and search for a YouTube channel
2. Browse the channel's videos and select ones you want to analyze
3. Click "Analyze Selected Videos" to generate AI-powered insights
4. Navigate to the **Q&A** page to ask questions about the content
5. Try the **Digest** feature to analyze multiple channels at once

Need more help? Check out the **About** page for detailed information.
""")
st.markdown('</div>', unsafe_allow_html=True)

# Stats and info section
if 'analyzed_videos' in st.session_state and st.session_state.analyzed_videos:
    st.markdown('<div class="section-header">Your Activity</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Analyzed Videos", len(st.session_state.analyzed_videos))

    with col2:
        if 'reports' in st.session_state and st.session_state.reports:
            st.metric("Available Reports", len(st.session_state.reports))
        else:
            st.metric("Available Reports", 0)

    with col3:
        if 'past_questions' in st.session_state and st.session_state.past_questions:
            st.metric("Questions Asked", len(st.session_state.past_questions))
        else:
            st.metric("Questions Asked", 0)

    # Show recent activity
    if st.session_state.analyzed_videos:
        with st.expander("Recently Analyzed Videos"):
            for video in st.session_state.analyzed_videos[-3:]:
                st.markdown(f"**{video['video_title']}**")
                if 'summary' in video:
                    summary = video['summary']
                    if len(summary) > 150:
                        summary = summary[:150] + "..."
                    st.markdown(summary)
                st.markdown("---")

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 30px; padding: 20px; font-size: 0.8rem; color: #888;">
    <p>YouTube Analyzer | Powered by Streamlit, YouTube API, and Anthropic Claude</p>
    <p>Made with ❤️ for efficient content research</p>
</div>
""", unsafe_allow_html=True)
