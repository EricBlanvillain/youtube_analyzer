# YouTube Analyzer User Guide

This guide provides detailed instructions on how to use the YouTube Analyzer application and all of its features.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Channel Analysis](#channel-analysis)
3. [Video Selection & Analysis](#video-selection--analysis)
4. [Asking Questions](#asking-questions)
5. [Managing Favorites](#managing-favorites)
6. [Vector Database Management](#vector-database-management)
7. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation & Setup

Ensure you have first followed the installation steps in the README.md file:

1. Install dependencies: `pip install -r requirements.txt`
2. Create and configure your `.env` file with the required API keys
3. Start the application with either:
   - Command line: `python main.py`
   - Web interface: `streamlit run app.py`

### Home Screen

The home screen provides access to three main functions:
- **Channel Analysis**: Search for YouTube channels and analyze their content
- **Ask Questions**: Query analyzed videos for specific information
- **Vector Database**: Manage the vector database for efficient retrieval

Click on any of these buttons to navigate to the respective section.

## Channel Analysis

The Channel Analysis page allows you to search for YouTube channels and select videos to analyze.

### Searching for Channels

You can find channels in three ways:

1. **Search by Name**:
   - Enter a channel name in the search box and click "Search"
   - The app will attempt to find the channel and display its videos

2. **Browse Popular Channels**:
   - Select a category from the dropdown menu
   - Browse through curated lists of channels in categories like:
     - Health & Wellness
     - Fitness
     - Technology
     - AI & Machine Learning
     - Programming
     - Science & Education
     - French Content
     - French Tech & AI
   - Click "Select" next to any channel to load its videos

3. **My Favorites**:
   - Channels you've marked as favorites will appear here
   - Click "Select" next to any favorite channel to load its videos

### Recent Searches

The application tracks your recent searches for convenience. Click on any recent search to quickly return to that channel.

## Video Selection & Analysis

### Filtering & Sorting Videos

Once you've selected a channel, you can filter and sort the list of videos:

- **Duration Filter**:
  - All
  - Short (<5min)
  - Medium (5-20min)
  - Long (>20min)

- **Search in Titles**:
  - Enter keywords to search within video titles

- **Sort By**:
  - Most Recent
  - Most Viewed
  - Longest
  - Shortest

### Selecting Videos

- Use the multiselect dropdown to choose videos for analysis
- Click "Analyze Selected Videos" to begin the analysis process
- The application will display a progress bar during analysis

### Viewing Video Details

- Select a single video and click "View Selected Video Details" to see information before analysis
- Details include:
  - Thumbnail
  - Title
  - Channel
  - Published date
  - Views, duration, likes, comments
  - Full description
  - Tags (if available)

### Analysis Results

After analysis is complete, each video will have an expandable section showing:

1. **Summary Tab**:
   - Overall summary
   - Detailed summary
   - Tone and style
   - Target audience
   - Content quality

2. **Key Points Tab**:
   - Bullet points of the main takeaways

3. **Topics Tab**:
   - List of main topics covered

4. **Important Facts Tab**:
   - Notable statements and facts from the video

5. **Technical Details Tab**:
   - Technical information discussed in the video

6. **Examples & Segments Tab**:
   - Examples and stories mentioned
   - Important segments or timestamps

## Asking Questions

The Q&A page allows you to ask questions about videos you've already analyzed.

### Asking General Questions

1. Navigate to the "Ask Questions" page
2. Enter your question in the text box
3. Click "Ask Question"
4. The AI will process your query and provide an answer based on all analyzed videos

### Limiting Questions to Specific Videos

1. Check the "Limit question to specific videos" box
2. Select which videos to include in the multiselect dropdown
3. Enter your question
4. Click "Ask Question"
5. The AI will only consider the selected videos when answering

### Using Example Questions

The application provides example questions that you can use:
1. Select an example from the dropdown
2. Click "Use This Example"
3. The question will be filled in automatically
4. Click "Ask Question" to proceed

### Follow-up Questions

After receiving an answer, you can:
1. Click "Ask a follow-up question" to continue the conversation
2. Enter a new question related to the previous context

## Managing Favorites

You can mark channels as favorites for easy access:

1. In the "Browse Popular Channels" tab, click the star (☆) next to any channel
2. The star will change to filled (⭐) indicating it's a favorite
3. Access all favorites under the "My Favorites" tab
4. Remove a channel from favorites by clicking the star again

## Vector Database Management

The Vector Database page allows you to manage the internal vector database used for efficient question answering.

### Database Statistics

View statistics about your vector database:
- Reports Indexed
- Transcripts Indexed
- Total Chunks

### Database Management Functions

1. **Reindex All Data**:
   - Rebuilds the vector database with all existing reports and transcripts
   - Use this if you're experiencing issues with retrieval quality

2. **Clear Embedding Cache**:
   - Clears the cache to free up disk space

3. **Fix Incomplete Reports**:
   - Identifies and reprocesses reports that were not properly generated
   - Can fix all incomplete reports or a specific video ID

### Testing Retrieval

Use the Test Retrieval section to check how the vector database works:
1. Enter a test query
2. Set the number of results to retrieve
3. Click "Run Test Query"
4. Review the retrieved chunks and their relevance scores

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Check your API keys in the `.env` file
   - Ensure your YouTube API key has not exceeded quota limits
   - Verify your Anthropic API key is properly formatted (`sk-ant-...`)

2. **Video Analysis Failures**:
   - Some videos may not have transcripts available
   - Very long videos might time out during analysis
   - Videos in languages other than English may produce incomplete analysis

3. **Channel Not Found**:
   - Try the exact channel handle or ID instead of the display name
   - Check if the channel is accessible in your region

4. **Poor Quality Answers**:
   - Try reindexing the vector database
   - Ask more specific questions
   - Analyze more videos from the channel for better context

For more detailed technical troubleshooting, please refer to the README.md file.
