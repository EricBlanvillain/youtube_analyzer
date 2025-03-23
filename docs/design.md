# YouTube Analyzer Design Document

This document outlines the design and architecture of the YouTube Analyzer project.

## Overview

YouTube Analyzer is a tool that allows users to analyze YouTube videos using AI. The application follows a modular architecture with separate components (agents) for different responsibilities.

## Architecture

The project follows a modular architecture organized around the following main components:

### 1. Workflow Orchestrator

The orchestrator is the central component that coordinates all activities in the application. It:

- Manages the overall workflow
- Handles user interactions
- Coordinates other components
- Maintains session state

**Key File**: `src/orchestrator.py`

### 2. Data Retriever

The data retriever is responsible for interacting with the YouTube API to:

- Fetch channel information
- Retrieve lists of videos
- Filter videos to exclude shorts
- Gather video metadata

**Key File**: `src/data_retriever.py`

### 3. Report Generator

The report generator handles:

- Downloading video transcripts
- Sending transcripts to the Anthropic API for analysis
- Storing and formatting analysis results
- Managing local storage of reports and transcripts

**Key File**: `src/report_generator.py`

### 4. QA Agent

The QA agent handles user queries about analyzed videos:

- Interfaces with stored reports
- Sends user questions to the Anthropic API
- Formats and returns answers
- Manages retrieval of reports and transcripts

**Key File**: `src/qa_agent.py`

### 5. Configuration Utilities

Configuration utilities handle loading and validating environment variables and application settings.

**Key File**: `utils/config.py`

## Data Flow

1. **Channel and Video Selection**:
   - User inputs a channel name
   - Data Retriever fetches channel info and video list
   - Orchestrator presents list to user and handles selection

2. **Video Analysis**:
   - For each selected video:
     - Report Generator downloads transcript
     - Report Generator sends transcript to Anthropic API
     - Report Generator saves analysis report locally

3. **Question Answering**:
   - User asks a question
   - QA Agent retrieves relevant reports
   - QA Agent sends question + report data to Anthropic API
   - QA Agent returns answer to user

## Data Storage

The application uses local file storage for:

- Video transcripts (as text files)
- Analysis reports (as JSON files)
- Session data (as JSON files)

Future enhancements could include integration with Supabase for persistent cloud storage.

## External Services

The application integrates with the following external services:

1. **YouTube Data API**:
   - Used to fetch channel and video information
   - Required authentication: API Key

2. **YouTube Transcript API**:
   - Used to download video transcripts
   - No authentication required

3. **Anthropic API (Claude)**:
   - Used for analyzing transcripts and answering questions
   - Required authentication: API Key

4. **Supabase** (future enhancement):
   - Used for persistent storage of reports
   - Required authentication: URL and API Key

## Key Workflows

### 1. Channel Analysis Workflow

```
Start → Input Channel Name → Fetch Channel Info →
List Videos → Select Videos →
For Each Video → Download Transcript → Analyze → Save Report →
End
```

### 2. Question Answering Workflow

```
Start → Input Question → Retrieve Reports →
Send Question + Reports to Claude →
Format Answer → Display Answer → End
```

## Future Enhancements

1. **Supabase Integration**:
   - Implement persistent storage of reports
   - Add user authentication
   - Enable sharing of analyzed videos

2. **UI Improvements**:
   - Web interface for easier interaction
   - Visualization of video analysis

3. **Analysis Improvements**:
   - Sentiment analysis of videos
   - Topic extraction and categorization
   - Comparative analysis between videos
