#!/usr/bin/env python3
"""
Streamlit page for generating digest reports from multiple YouTube channels.
This page allows users to get summaries and insights from multiple channels at once.
"""
import streamlit as st
import time
import ssl
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

from src.orchestrator import WorkflowOrchestrator
from utils.config import config

# Initialize session state variables if they don't exist
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = WorkflowOrchestrator()
if 'digest' not in st.session_state:
    st.session_state.digest = None
if 'digest_channels' not in st.session_state:
    st.session_state.digest_channels = []
if 'digest_processing' not in st.session_state:
    st.session_state.digest_processing = False

# Try to automatically load the most recent digest if none is in session state
if st.session_state.digest is None:
    try:
        import glob
        import os
        import json

        # Find all digest files and sort by modification time (most recent first)
        digest_files = glob.glob(os.path.join(st.session_state.orchestrator.data_dir, "digest_*.json"))

        if digest_files:
            # Sort by modification time, newest first
            digest_files.sort(key=os.path.getmtime, reverse=True)
            most_recent = digest_files[0]

            # Load the digest
            with open(most_recent, 'r') as f:
                st.session_state.digest = json.load(f)
            print(f"Automatically loaded digest from file: {os.path.basename(most_recent)}")
    except Exception as e:
        print(f"Error auto-loading digest file: {e}")

def display_digest_page():
    """Display the digest page for analyzing multiple channels."""
    st.markdown('<div class="main-title">YouTube Channel Digest</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Generate summaries and insights from multiple YouTube channels</div>', unsafe_allow_html=True)

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

    # Create tabs for setup, results, and troubleshooting
    setup_tab, results_tab, troubleshoot_tab = st.tabs(["Setup Digest", "View Results", "Troubleshooting"])

    with setup_tab:
        st.markdown('<div class="section-header">Channel Digest Configuration</div>', unsafe_allow_html=True)

        # Digest type selection
        digest_type = st.selectbox(
            "Digest Type",
            ["weekly", "monthly", "trending"],
            index=0,
            help="Select the type of digest to generate"
        )

        # Number of videos per channel
        videos_per_channel = st.slider(
            "Videos Per Channel",
            min_value=1,
            max_value=10,
            value=3,
            help="Number of recent videos to include from each channel"
        )

        # Channel input section
        st.markdown("### Select YouTube Channels")
        st.markdown("Choose from suggested channels by category or enter custom channel names.")

        # Initialize session state for selected channels if not exists
        if 'selected_channels' not in st.session_state:
            st.session_state.selected_channels = set()

        # Create tabs for different input methods
        channel_tabs = st.tabs(["Suggested Channels", "Custom Channels"])

        with channel_tabs[0]:
            # Define channel categories and their channels
            channel_categories = {
                "AI & Machine Learning": {
                    "DeepLearningAI": "Andrew Ng's deep learning courses and AI news",
                    "Two Minute Papers": "AI research simplified",
                    "Yannic Kilcher": "In-depth ML paper explanations",
                    "TheAIGRID": "AI news and tutorials",
                    "AI Explained": "Clear explanations of AI concepts",
                    "Computerphile": "Computer science and AI topics",
                    "Sentdex": "Python and AI tutorials",
                    "Machine Learning Street Talk": "ML researcher interviews"
                },
                "Tech & Programming": {
                    "Fireship": "Quick, modern web development tutorials",
                    "Tech With Tim": "Python and programming tutorials",
                    "CodeWithHarry": "Web development and programming",
                    "Traversy Media": "Full-stack development tutorials",
                    "The Net Ninja": "Web development tutorials",
                    "Web Dev Simplified": "Web development concepts explained",
                    "Programming with Mosh": "Programming language tutorials",
                    "freeCodeCamp": "Comprehensive programming courses"
                },
                "Science & Education": {
                    "Veritasium": "Science and engineering explained",
                    "3Blue1Brown": "Beautiful math animations",
                    "Kurzgesagt": "Science topics with amazing animations",
                    "MinutePhysics": "Physics concepts explained briefly",
                    "SmarterEveryDay": "Science and engineering experiments",
                    "Physics Girl": "Physics experiments and explanations",
                    "Vsauce": "Mind-bending science topics",
                    "Numberphile": "Mathematics explained"
                },
                "Tech News & Reviews": {
                    "MKBHD": "High-quality tech reviews",
                    "Linus Tech Tips": "Tech reviews and news",
                    "Dave2D": "Minimalist tech reviews",
                    "Unbox Therapy": "Latest tech unboxing",
                    "The Verge": "Tech news and reviews",
                    "Austin Evans": "Tech reviews and comparisons",
                    "TechLinked": "Daily tech news updates",
                    "Engadget": "Tech news and reviews"
                },
                "Fitness & Health": {
                    "ATHLEAN-X": "Science-based fitness advice and workouts",
                    "Jeff Nippard": "Evidence-based training and nutrition",
                    "Jeremy Ethier": "Science-explained fitness and nutrition",
                    "Hybrid Calisthenics": "Progressive bodyweight fitness",
                    "FitnessBlender": "Full-length workout videos",
                    "What I've Learned": "Health and nutrition deep dives",
                    "HealthLine": "Evidence-based health information",
                    "Mind Pump TV": "Fitness and health education"
                },
                "General News": {
                    "Reuters": "Global news coverage",
                    "Associated Press": "Breaking news and investigations",
                    "DW News": "International news and documentaries",
                    "PBS NewsHour": "In-depth news analysis",
                    "Al Jazeera English": "Global news perspective",
                    "Bloomberg": "Business and financial news",
                    "Vox": "Explanatory journalism",
                    "TLDR News": "Simplified news explanations"
                }
            }

            # Display channels by category with checkboxes
            for category, channels in channel_categories.items():
                with st.expander(f"{category} ({len(channels)} channels)"):
                    st.markdown(f"**{category}**")
                    cols = st.columns(2)
                    for i, (channel, description) in enumerate(channels.items()):
                        col = cols[i % 2]
                        with col:
                            channel_key = f"{category}_{channel}"
                            if st.checkbox(
                                f"{channel}",
                                help=description,
                                key=channel_key,
                                value=channel in st.session_state.selected_channels
                            ):
                                st.session_state.selected_channels.add(channel)
                            else:
                                st.session_state.selected_channels.discard(channel)

            # Show currently selected channels
            if st.session_state.selected_channels:
                st.markdown("### Selected Channels")
                st.markdown(", ".join(sorted(st.session_state.selected_channels)))

        with channel_tabs[1]:
            st.markdown("Enter custom channel names (one per line):")
            custom_channels = st.text_area(
                "Custom Channels",
                height=150,
                placeholder="e.g., TechChannel\nScienceChannel\nAIChannel"
            )

        # Combine selected and custom channels
        channel_names = list(st.session_state.selected_channels)
        if custom_channels:
            custom_channel_list = [name.strip() for name in custom_channels.split("\n") if name.strip()]
            channel_names.extend(custom_channel_list)

        # Show total number of channels selected
        if channel_names:
            st.info(f"Total channels selected: {len(channel_names)}")

        # Advanced options (collapsible)
        with st.expander("Advanced Options"):
            use_ssl_workaround = st.checkbox(
                "Enable SSL/TLS workaround",
                value=False,
                help="Use this if you encounter SSL/TLS connection issues"
            )

            retry_count = st.number_input(
                "Retry Count",
                min_value=1,
                max_value=10,
                value=3,
                help="Number of retries for API calls in case of errors"
            )

        # Generate button
        submit_button = st.button("Generate Digest")

        if submit_button:
            # Store the channel names and options in session state
            st.session_state.digest_channels = channel_names
            st.session_state.digest_processing = True
            st.session_state.use_ssl_workaround = use_ssl_workaround
            st.session_state.retry_count = retry_count
            st.session_state.digest = None  # Reset any existing digest
            st.rerun()

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

                # Track videos with disabled transcripts
                videos_with_issues = []
                valid_videos = []

                # Get the report generator
                report_generator = st.session_state.orchestrator.report_generator

                # Process each video and track transcript availability
                for channel_info, videos in channel_videos:
                    for video in videos:
                        try:
                            # Try to get the transcript - if it fails, the transcript is not available
                            transcript = data_retriever.get_transcript(video["id"])
                            if transcript:
                                valid_videos.append(video)
                            else:
                                videos_with_issues.append({
                                    "title": video["title"],
                                    "channel": channel_info["title"],
                                    "reason": "Transcript not available"
                                })
                        except Exception as e:
                            videos_with_issues.append({
                                "title": video["title"],
                                "channel": channel_info["title"],
                                "reason": f"Error accessing transcript: {str(e)}"
                            })

                # Show transcript availability status
                if videos_with_issues:
                    st.warning("Some videos cannot be analyzed due to unavailable transcripts:")
                    for video in videos_with_issues:
                        st.markdown(f"- **{video['title']}** from {video['channel']}: {video['reason']}")

                if not valid_videos:
                    st.error("No videos with available transcripts found. Please try different channels or videos.")
                    st.info("Tips for finding videos with transcripts:")
                    st.markdown("""
                    - Look for educational content and tutorials
                    - Choose videos with English audio
                    - Select videos from channels that regularly provide captions
                    - Recent videos from major tech channels often have auto-generated transcripts
                    """)
                    st.session_state.digest_processing = False
                    return

                status_text.text(f"Found {len(valid_videos)} videos with available transcripts. Proceeding with analysis...")
                progress_bar.progress(40)

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
                            # Create a complete video info structure with all required fields
                            video_info = {
                                "id": video["id"],
                                "title": video["title"],
                                "video_title": video["title"],  # Required for vector store
                                "channel_title": channel_info["title"],
                                "channel": {
                                    "id": channel_info["id"],
                                    "name": channel_info["title"]
                                },
                                "published_at": video.get("published_at", ""),
                                "duration": video.get("duration", ""),
                                "view_count": video.get("view_count", "0"),
                                "like_count": video.get("like_count", "0"),
                                "comment_count": video.get("comment_count", "0")
                            }
                            all_videos.append(video_info)

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

        # Display digest if available
        if st.session_state.digest:
            st.markdown('<div class="section-header">Digest Results</div>', unsafe_allow_html=True)
            st.markdown('<div class="card">', unsafe_allow_html=True)

            # Display digest title and date
            st.markdown(f"# {st.session_state.digest.get('title', 'Content Digest')}")
            st.markdown(f"**Generated on:** {st.session_state.digest.get('date', 'Unknown date')}")

            # Display executive summary if available
            if "executive_summary" in st.session_state.digest:
                st.markdown("## Executive Summary")
                st.markdown(st.session_state.digest["executive_summary"])

            # Display content categories
            if "content_categories" in st.session_state.digest:
                st.markdown("## Content Categories")
                for category in st.session_state.digest["content_categories"]:
                    st.markdown(f"### {category['category']}")

                    # Key Developments
                    if category.get('key_developments'):
                        st.markdown("#### Key Developments")
                        for dev in category['key_developments']:
                            st.markdown(f"**{dev['title']}**")
                            st.markdown(dev['description'])
                            st.markdown(f"*Impact:* {dev['impact']}")
                            if dev.get('source_videos'):
                                st.markdown("*Sources:* " + ", ".join(dev['source_videos']))
                            st.markdown("---")

                    # Emerging Trends
                    if category.get('emerging_trends'):
                        st.markdown("#### Emerging Trends")
                        for trend in category['emerging_trends']:
                            st.markdown(f"**{trend['trend']}**")
                            st.markdown(trend['description'])
                            if trend.get('evidence'):
                                st.markdown("*Evidence:* " + ", ".join(trend['evidence']))
                            if trend.get('implications'):
                                st.markdown(f"*Implications:* {trend['implications']}")
                            st.markdown("---")

            # Display cross-category insights
            if "cross_category_insights" in st.session_state.digest:
                st.markdown("## Cross-Category Insights")
                for insight in st.session_state.digest["cross_category_insights"]:
                    st.markdown(f"### {insight['topic']}")
                    st.markdown(insight['description'])
                    if insight.get('categories'):
                        st.markdown("*Related Categories:* " + ", ".join(insight['categories']))
                    if insight.get('key_points'):
                        st.markdown("**Key Points:**")
                        for point in insight['key_points']:
                            st.markdown(f"- {point}")
                    if insight.get('source_videos'):
                        st.markdown("*Sources:* " + ", ".join(insight['source_videos']))
                    st.markdown("---")

            # Display featured content
            if "featured_content" in st.session_state.digest:
                st.markdown("## Featured Content")
                featured = st.session_state.digest["featured_content"]
                st.markdown(f"### {featured['title']}")
                st.markdown(featured['description'])
                if featured.get('key_points'):
                    st.markdown("**Key Points:**")
                    for point in featured['key_points']:
                        st.markdown(f"- {point}")
                if featured.get('current_state'):
                    st.markdown(f"**Current State:** {featured['current_state']}")
                if featured.get('future_potential'):
                    st.markdown(f"**Future Potential:** {featured['future_potential']}")
                if featured.get('related_videos'):
                    st.markdown("*Related Videos:* " + ", ".join(featured['related_videos']))

            # Display notable insights
            if "notable_insights" in st.session_state.digest:
                st.markdown("## Notable Insights")
                for insight in st.session_state.digest["notable_insights"]:
                    with st.container():
                        st.markdown(f"### {insight['category']}")
                        st.markdown(f"**Insight:** {insight['insight']}")
                        st.markdown(f"**Explanation:** {insight['explanation']}")
                        if insight.get('practical_value'):
                            st.markdown(f"**Practical Value:** {insight['practical_value']}")
                        if insight.get('source'):
                            st.markdown(f"*Source:* {insight['source']}")
                        st.markdown("---")

            # Display video summaries
            if "video_summaries" in st.session_state.digest:
                st.markdown("## Video Summaries")
                for summary in st.session_state.digest["video_summaries"]:
                    with st.container():
                        st.markdown(f"### {summary['video_title']}")
                        st.markdown(f"*Channel:* {summary['channel_title']}")
                        if summary.get('category'):
                            st.markdown(f"*Category:* {summary['category']}")
                        st.markdown(f"**Highlights:** {summary['highlights']}")
                        if summary.get('main_topics'):
                            st.markdown("**Main Topics:**")
                            for topic in summary['main_topics']:
                                st.markdown(f"- {topic}")
                        if summary.get('key_points'):
                            st.markdown("**Key Points:**")
                            for point in summary['key_points']:
                                st.markdown(f"- {point}")
                        if summary.get('practical_takeaways'):
                            st.markdown("**Practical Takeaways:**")
                            for takeaway in summary['practical_takeaways']:
                                st.markdown(f"- {takeaway}")
                        if summary.get('relevance'):
                            st.markdown(f"*Relevance:* {summary['relevance']}")
                        st.markdown("---")

            # Display recommendations
            if "recommendations" in st.session_state.digest:
                st.markdown("## Recommendations")
                for rec in st.session_state.digest["recommendations"]:
                    st.markdown(f"### For {rec['audience']}")
                    if rec.get('recommended_videos'):
                        st.markdown("**Recommended Videos:**")
                        for video in rec['recommended_videos']:
                            st.markdown(f"- {video['title']}")
                            if video.get('reason'):
                                st.markdown(f"  *Why:* {video['reason']}")
                    if rec.get('key_themes'):
                        st.markdown("**Key Themes:**")
                        for theme in rec['key_themes']:
                            st.markdown(f"- {theme}")
                    if rec.get('practical_value'):
                        st.markdown(f"**Value for Audience:** {rec['practical_value']}")
                    st.markdown("---")

            st.markdown('</div>', unsafe_allow_html=True)

            # Add option to regenerate
            if st.button("Generate New Digest"):
                st.session_state.digest = None
                st.rerun()

        # Show message if no digest available
        elif not st.session_state.digest_processing:
            st.info("No digest available. Please go to the Setup Digest tab to generate a new digest.")

            # Try to load the most recent digest file
            try:
                import glob
                import os
                import json

                # Find all digest files and sort by modification time (most recent first)
                digest_files = glob.glob(os.path.join(st.session_state.orchestrator.data_dir, "digest_*.json"))

                if digest_files:
                    # Sort by modification time, newest first
                    digest_files.sort(key=os.path.getmtime, reverse=True)
                    most_recent = digest_files[0]

                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if st.button("📄 Load Recent Digest"):
                            with open(most_recent, 'r') as f:
                                digest_data = json.load(f)
                            st.session_state.digest = digest_data
                            st.success("Loaded digest successfully!")
                            st.rerun()
                    with col2:
                        st.markdown(f"*Found a saved digest from {os.path.basename(most_recent).split('_')[1].split('.')[0]}*")
            except Exception as e:
                st.error(f"Error loading digest file: {e}")

    with troubleshoot_tab:
        st.markdown('<div class="section-header">Troubleshooting SSL/TLS Issues</div>', unsafe_allow_html=True)

        st.markdown("""
        ## Common SSL/TLS Issues

        If you're experiencing SSL/TLS connection errors when generating digests, try the following solutions:

        ### 1. Enable SSL/TLS Workaround

        - Go to the "Setup Digest" tab
        - Expand the "Advanced Options" section
        - Check the "Enable SSL/TLS workaround" option
        - Try generating the digest again

        ### 2. Update Python and OpenSSL

        SSL/TLS issues are often caused by outdated SSL libraries. Make sure you have the latest version of Python and OpenSSL installed.

        ### 3. Check Network Settings

        Some network security settings, firewalls, or VPNs can interfere with SSL/TLS connections. Try:
        - Connecting to a different network
        - Temporarily disabling VPN or proxy settings
        - Checking if your organization has specific SSL/TLS policies

        ### 4. Run SSL Diagnostics

        You can run the following command to test your SSL connection to the Anthropic API:
        ```
        python -c "import requests; print(requests.get('https://api.anthropic.com').status_code)"
        ```

        If this returns a status code of 404 or similar, your basic SSL connection is working.

        ### 5. Contact Support

        If none of these solutions work, please contact support with:
        - Your operating system and version
        - Your Python version
        - The exact error message you're receiving
        """)

        # Add a button to test Anthropic API connection
        if st.button("Test Anthropic API Connection"):
            try:
                # Create a simple request to the Anthropic API
                response = requests.get('https://api.anthropic.com')
                if response.status_code == 404:  # Expected for unauthorized access
                    st.success("SSL connection to Anthropic API is working properly!")
                else:
                    st.info(f"Received status code {response.status_code} from Anthropic API. This is unexpected but not necessarily an error.")
            except requests.exceptions.SSLError as e:
                st.error(f"SSL Error: {str(e)}")
                st.error("Your SSL configuration is having issues connecting to the Anthropic API.")
                st.info("Try enabling the SSL/TLS workaround in Advanced Options.")
            except Exception as e:
                st.error(f"Error connecting to Anthropic API: {str(e)}")

# Run the app
display_digest_page()
