#!/usr/bin/env python3
"""
Streamlit page with information about the YouTube Analyzer app.
This page provides information about the application, its features, and usage instructions.
"""
import streamlit as st

# Apply custom styling
def display_about_page():
    """Display the about page."""
    st.markdown('<div class="main-title">About YouTube Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Learn more about this application and how to use it</div>', unsafe_allow_html=True)

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

# Run the app
display_about_page()
