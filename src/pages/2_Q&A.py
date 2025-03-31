#!/usr/bin/env python3
"""
Streamlit page for asking questions about analyzed YouTube videos.
This page allows users to ask questions about videos they've analyzed.
"""
import streamlit as st
import pandas as pd
import time

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
if 'past_questions' not in st.session_state:
    st.session_state.past_questions = []

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

    # Add to past questions
    if 'past_questions' not in st.session_state:
        st.session_state.past_questions = []

    st.session_state.past_questions.append({
        "question": question,
        "answer": answer,
        "video_ids": video_ids,
        "timestamp": pd.Timestamp.now()
    })

def display_qa_page():
    """Display the Q&A page."""
    st.markdown('<div class="main-title">Ask Questions About Videos</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Get answers to specific questions about analyzed YouTube videos</div>', unsafe_allow_html=True)

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

    # Ensure we have the reports list
    if 'reports' not in st.session_state or not st.session_state.reports:
        st.session_state.reports = st.session_state.orchestrator.qa_agent.list_available_reports()

    # Main Q&A interface
    if not st.session_state.reports:
        st.warning("No analyzed videos found. Please go to the Analyze page and analyze some videos first.")
        st.info("Once you've analyzed videos, you can ask questions about their content here.")
    else:
        st.markdown('<div class="section-header">Ask a Question</div>', unsafe_allow_html=True)

        # Option to select specific videos
        st.checkbox("Only search in specific videos", key="specific_videos")

        if st.session_state.get('specific_videos', False):
            if st.session_state.reports:
                # Create labels for the videos
                labels = [f"{r['video_title']}" for r in st.session_state.reports]
                options = list(range(len(labels)))

                # Create the multiselect
                st.multiselect(
                    "Select videos to search:",
                    options=options,
                    format_func=lambda i: labels[i],
                    key="qa_video_selection"
                )

        # Question input
        st.text_area("Type your question:",
                    key="question",
                    placeholder="e.g., 'What are the main points discussed in the video?' or 'Explain the concept of [specific topic] mentioned in the video.'")

        # Add a button to submit the question
        if st.button("Ask Question", key="submit_question"):
            ask_question()

        # Display the answer if available
        if 'answer' in st.session_state and st.session_state.answer:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### Answer")
            st.markdown(st.session_state.answer)
            st.markdown('</div>', unsafe_allow_html=True)

        # Show past questions if available
        if 'past_questions' in st.session_state and st.session_state.past_questions:
            st.markdown('<div class="section-header">Question History</div>', unsafe_allow_html=True)

            for i, qa in enumerate(reversed(st.session_state.past_questions)):
                with st.expander(f"Q: {qa['question'][:80]}..." if len(qa['question']) > 80 else f"Q: {qa['question']}"):
                    st.markdown(f"**Question:** {qa['question']}")
                    st.markdown(f"**Answer:** {qa['answer']}")

                    if qa['video_ids']:
                        # Find video titles
                        video_titles = []
                        for vid_id in qa['video_ids']:
                            for report in st.session_state.reports:
                                if report['video_id'] == vid_id:
                                    video_titles.append(report['video_title'])

                        if video_titles:
                            st.markdown("**Videos queried:**")
                            for title in video_titles:
                                st.markdown(f"- {title}")

                    st.markdown(f"*Asked on {qa['timestamp'].strftime('%Y-%m-%d %H:%M')}*")

        # Show suggested questions
        st.markdown('<div class="section-header">Suggested Questions</div>', unsafe_allow_html=True)

        # Group suggested questions by category
        suggested_questions = {
            "General": [
                "What is the main topic of this video?",
                "Summarize the key points made in the video.",
                "What is the overall conclusion of this video?"
            ],
            "Technical": [
                "Explain the technical concepts discussed in this video.",
                "What tools or technologies were mentioned?",
                "How does [specific technology mentioned] work?"
            ],
            "Practical": [
                "What practical examples were given in the video?",
                "How can I apply the concepts from this video?",
                "What are the steps to implement what was taught?"
            ]
        }

        # Create tabs for question categories
        question_tabs = st.tabs(list(suggested_questions.keys()))

        for i, (category, questions) in enumerate(suggested_questions.items()):
            with question_tabs[i]:
                for q in questions:
                    if st.button(q, key=f"suggested_{category}_{q}"):
                        st.session_state.question = q
                        ask_question()

# Run the app
display_qa_page()
