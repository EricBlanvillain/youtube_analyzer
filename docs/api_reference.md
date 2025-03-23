# API Reference

This document provides detailed information about the APIs and modules in the YouTube Analyzer application.

## Table of Contents

1. [Orchestrator](#orchestrator)
2. [Data Retriever](#data-retriever)
3. [Report Generator](#report-generator)
4. [QA Agent](#qa-agent)
5. [Vector Store](#vector-store)
6. [Configuration](#configuration)

## Orchestrator

`src/orchestrator.py`

The central component that coordinates all activities in the application.

### Class: WorkflowOrchestrator

The main orchestrator class that manages the application workflow.

#### Methods

| Method | Description | Parameters | Return Value |
|--------|-------------|------------|-------------|
| `__init__()` | Initializes the orchestrator and dependencies | None | None |
| `analyze_channel(channel_name)` | Analyzes a YouTube channel | `channel_name` (str): The name of the channel | Tuple: (channel_info, videos) |
| `select_videos(indices)` | Selects videos for analysis | `indices` (list): List of video indices | List of selected videos |
| `analyze_videos(videos)` | Analyzes the selected videos | `videos` (list): List of video objects | List of analysis reports |
| `ask_question(question, video_ids=None)` | Asks a question about analyzed videos | `question` (str): The user's question<br>`video_ids` (list, optional): List of specific video IDs to query | String response |

## Data Retriever

`src/data_retriever.py`

Handles all interactions with the YouTube API to retrieve channel and video information.

### Class: YouTubeDataRetriever

Responsible for YouTube API interactions.

#### Methods

| Method | Description | Parameters | Return Value |
|--------|-------------|------------|-------------|
| `__init__(api_key)` | Initializes with YouTube API key | `api_key` (str): YouTube API key | None |
| `get_channel_id(channel_name)` | Gets channel ID from name | `channel_name` (str): The channel name/handle | String ID or None |
| `get_channel_info(channel_id)` | Gets channel details | `channel_id` (str): The channel ID | Dict of channel information |
| `get_channel_videos(channel_id, max_results=50)` | Gets videos from a channel | `channel_id` (str): The channel ID<br>`max_results` (int): Maximum videos to retrieve | List of video objects |
| `get_channel_and_videos(channel_name)` | Gets channel info and videos | `channel_name` (str): The channel name/handle | Tuple: (channel_info, videos) |

## Report Generator

`src/report_generator.py`

Handles video transcript retrieval and analysis using the Anthropic API.

### Class: ReportGenerator

Generates analysis reports from video transcripts.

#### Methods

| Method | Description | Parameters | Return Value |
|--------|-------------|------------|-------------|
| `__init__(api_key)` | Initializes with Anthropic API key | `api_key` (str): Anthropic API key | None |
| `get_transcript(video_id)` | Retrieves video transcript | `video_id` (str): YouTube video ID | String transcript or None |
| `analyze_transcript(video, transcript)` | Analyzes a video transcript | `video` (dict): Video information<br>`transcript` (str): The video transcript | Dict containing analysis report |
| `save_report(report)` | Saves analysis report | `report` (dict): The analysis report | None |
| `load_report(video_id)` | Loads a saved report | `video_id` (str): YouTube video ID | Dict report or None |

## QA Agent

`src/qa_agent.py`

Handles user questions about analyzed videos using the Anthropic API.

### Class: QuestionAnsweringAgent

Answers questions about analyzed videos.

#### Methods

| Method | Description | Parameters | Return Value |
|--------|-------------|------------|-------------|
| `__init__(api_key)` | Initializes with Anthropic API key | `api_key` (str): Anthropic API key | None |
| `answer_question(question, reports)` | Answers a question | `question` (str): The user question<br>`reports` (list): List of analysis reports | String answer |
| `list_available_reports()` | Lists all available reports | None | List of report metadata |
| `get_report(video_id)` | Gets a specific report | `video_id` (str): YouTube video ID | Dict report or None |

## Vector Store

`src/vector_store.py`

Manages the vector database for efficient semantic retrieval of information.

### Class: VectorStore

Stores and retrieves vector embeddings for semantic search.

#### Methods

| Method | Description | Parameters | Return Value |
|--------|-------------|------------|-------------|
| `__init__()` | Initializes the vector store | None | None |
| `get_embedding(text)` | Gets embedding vector for text | `text` (str): Text to embed | List of floats (vector) |
| `add_report(report)` | Adds a report to the store | `report` (dict): The analysis report | None |
| `add_transcript(video_id, video_title, transcript)` | Adds a transcript | `video_id` (str): YouTube video ID<br>`video_title` (str): Video title<br>`transcript` (str): The transcript | None |
| `retrieve_relevant_chunks(query, n_results=5)` | Retrieves relevant chunks | `query` (str): The user query<br>`n_results` (int): Number of results | List of relevant chunks |
| `reindex_all_data()` | Rebuilds the vector database | None | None |
| `clear_cache()` | Clears the embedding cache | None | None |

### Vector Database Utilities

`src/vector_db_utils.py`

Utility functions for managing the vector database.

#### Functions

| Function | Description | Parameters | Return Value |
|----------|-------------|------------|-------------|
| `reprocess_incomplete_reports()` | Reprocesses reports with errors | None | List of fixed report IDs |
| `reprocess_specific_video(video_id)` | Reprocesses a specific video | `video_id` (str): YouTube video ID | Boolean success status |

## Configuration

`utils/config.py`

Handles application configuration and environment variables.

### Class: Config

Loads and provides access to application configuration.

#### Attributes

| Attribute | Description | Type |
|-----------|-------------|------|
| `youtube_api_key` | YouTube Data API key | String |
| `anthropic_api_key` | Anthropic API key | String |
| `max_videos` | Maximum videos to retrieve | Integer |
| `data_dir` | Directory for storing data | String |
| `reports_dir` | Directory for storing reports | String |
| `transcripts_dir` | Directory for storing transcripts | String |
| `embedding_cache_dir` | Directory for the embedding cache | String |
| `vector_db_dir` | Directory for vector database files | String |

## Integration Examples

### Example 1: Analyzing a Channel and Answering Questions

```python
from src.orchestrator import WorkflowOrchestrator

# Initialize the orchestrator
orchestrator = WorkflowOrchestrator()

# Analyze a channel
channel_info, videos = orchestrator.analyze_channel("Huberman Lab")

# Select the first three videos
selected_videos = orchestrator.select_videos([0, 1, 2])

# Analyze the selected videos
reports = orchestrator.analyze_videos(selected_videos)

# Ask a question about the videos
answer = orchestrator.ask_question("What are the main topics discussed about sleep?")
print(answer)
```

### Example 2: Using the Vector Store Directly

```python
from src.vector_store import VectorStore

# Initialize the vector store
vector_store = VectorStore()

# Search for relevant information
results = vector_store.retrieve_relevant_chunks(
    query="How does exercise affect dopamine levels?",
    n_results=3
)

# Display the results
for i, result in enumerate(results):
    print(f"Result {i+1}:")
    print(f"Video: {result['metadata']['video_title']}")
    print(f"Content: {result['chunk'][:100]}...")
    print(f"Relevance: {result['distance']:.4f}")
    print()
```

### Example 3: Processing a Single Video

```python
from src.orchestrator import WorkflowOrchestrator
from src.data_retriever import YouTubeDataRetriever
from src.report_generator import ReportGenerator
from utils.config import config

# Initialize components
data_retriever = YouTubeDataRetriever(config.youtube_api_key)
report_generator = ReportGenerator(config.anthropic_api_key)

# Get video information
video_id = "tNZnLkRBYA8"
video_info = data_retriever.get_video_info(video_id)

# Get transcript
transcript = report_generator.get_transcript(video_id)

# Analyze transcript
if transcript:
    report = report_generator.analyze_transcript(video_info, transcript)
    report_generator.save_report(report)
    print(f"Successfully analyzed video: {video_info['title']}")
```
