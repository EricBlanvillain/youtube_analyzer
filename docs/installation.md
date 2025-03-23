# Installation & Configuration Guide

This guide provides detailed instructions for installing and configuring the YouTube Analyzer application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [API Keys](#api-keys)
4. [Configuration](#configuration)
5. [Directory Structure](#directory-structure)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

Before installing YouTube Analyzer, ensure you have:

- **Python 3.8 or higher** installed on your system
- **pip** (Python package manager)
- Basic command-line knowledge
- Internet connection for API access
- Sufficient storage space for the databases and data files

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/youtube_analyzer.git
cd youtube_analyzer
```

### Step 2: Set Up a Virtual Environment (Optional but Recommended)

```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## API Keys

The application requires API keys for external services:

### YouTube Data API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3 for your project
4. Create an API key:
   - Navigate to "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy the generated key

**Note**: The YouTube Data API has quota limits. The free tier allows 10,000 units per day, and most requests cost between 1-100 units.

### Anthropic API (Claude)

1. Sign up at [Anthropic](https://console.anthropic.com/)
2. Navigate to the API section
3. Generate a new API key
4. Copy the key (it starts with `sk-ant-`)

**Note**: Anthropic API usage may incur charges based on your usage. Check their pricing page for details.

## Configuration

### Step 1: Create Environment File

Create a `.env` file in the project's root directory with the following contents:

```
# API Keys
YOUTUBE_API_KEY=your_youtube_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Application Settings
MAX_VIDEOS=50
MODEL_NAME=claude-3-sonnet-20240229

# Directory Settings
DATA_DIR=data
REPORTS_DIR=data/reports
TRANSCRIPTS_DIR=data/transcripts
EMBEDDING_CACHE_DIR=data/embedding_cache
VECTOR_DB_DIR=data/vector_db
```

Replace `your_youtube_api_key_here` and `your_anthropic_api_key_here` with your actual API keys.

### Step 2: Create Required Directories

The application needs certain directories for data storage. These will be created automatically on first run, but you can create them manually:

```bash
mkdir -p data/reports data/transcripts data/embedding_cache data/vector_db
```

## Directory Structure

Understanding the directory structure helps with troubleshooting and development:

```
youtube_analyzer/
├── app.py                 # Streamlit web application
├── main.py                # Command-line application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── .env.example           # Example environment file
├── README.md              # Project overview
├── src/                   # Source code
│   ├── __init__.py
│   ├── orchestrator.py    # Main workflow controller
│   ├── data_retriever.py  # YouTube API interactions
│   ├── report_generator.py # Transcript analysis
│   ├── qa_agent.py        # Question answering
│   ├── vector_store.py    # Vector database
│   └── vector_db_utils.py # Database utilities
├── utils/
│   ├── __init__.py
│   └── config.py          # Configuration loader
├── data/                  # Data storage (created on runtime)
│   ├── reports/           # Analysis reports
│   ├── transcripts/       # Video transcripts
│   ├── embedding_cache/   # Embedding vectors cache
│   └── vector_db/         # Vector database files
├── docs/                  # Documentation
│   ├── design.md          # Architecture design
│   ├── user_guide.md      # User guide
│   └── api_reference.md   # API documentation
└── tests/                 # Test files
```

## Running the Application

### Web Interface (Recommended)

```bash
streamlit run app.py
```

This will start the Streamlit web server and open the application in your browser.

### Command Line Interface

```bash
python main.py
```

This will start the interactive command-line interface.

## Troubleshooting

### Common Issues

#### API Key Authentication Errors

If you see an error like:
```
Error analyzing transcript: Error code: 401 - {'type': 'error', 'error': {'type': 'authentication_error', 'message': 'invalid x-api-key'}}
```

**Solution**:
- Double-check your API key in the `.env` file
- Ensure there are no extra spaces or characters
- Verify the key is still active

#### YouTube API Quota Exceeded

If you see an error like:
```
googleapiclient.errors.HttpError: <HttpError 403 when requesting ... returned "The request cannot be completed because you have exceeded your quota."
```

**Solution**:
- Wait until the quota resets (usually 24 hours)
- Create a new project in Google Cloud Console and get a new API key
- Reduce the number of requests by analyzing fewer videos

#### Missing Transcripts

If you see a message like:
```
Could not retrieve transcript for video: [Video Title]
```

**Solution**:
- The video might not have captions/transcripts available
- Try a different video from the same channel
- The video might use a language not supported by the transcript API

#### Installation Errors

If you encounter errors during installation:

**Solution**:
- Check your Python version: `python --version`
- Update pip: `pip install --upgrade pip`
- Install individual packages manually to identify the problematic one
- Try installing in a clean virtual environment

#### Database Errors

If you encounter vector database errors:

**Solution**:
- Try reindexing the database from the Vector Database management page
- Clear the embedding cache
- Delete the `data/vector_db` directory and let the application rebuild it
- Check file permissions if on Linux/macOS

### Advanced Troubleshooting

#### Debugging the Application

For more verbose logging, you can set the `LOGLEVEL` environment variable:

```bash
# For macOS/Linux
export LOGLEVEL=DEBUG
# For Windows
set LOGLEVEL=DEBUG
```

Then run the application as usual.

#### Testing API Connectivity

Test your API keys directly:

```python
# Test YouTube API
from googleapiclient.discovery import build
youtube = build('youtube', 'v3', developerKey='YOUR_API_KEY')
request = youtube.channels().list(part='snippet', forUsername='GoogleDevelopers')
response = request.execute()
print(response)

# Test Anthropic API
import anthropic
client = anthropic.Anthropic(api_key='YOUR_API_KEY')
message = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ]
)
print(message.content)
```

If these tests work but the application still fails, the issue might be in the application code.
