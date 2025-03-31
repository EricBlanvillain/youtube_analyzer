# YouTube Analyzer

A tool for analyzing YouTube content using AI. This application allows users to select and analyze videos from a specified YouTube channel, summarize content, and answer questions about the videos.

## Features

- Retrieve information about YouTube channels
- List and filter recent videos (excluding Shorts)
- Analyze video transcripts using Claude AI
- Store and retrieve analysis reports
- Answer questions about analyzed videos
- Generate multi-channel digests
- Vector database for semantic search

## Setup

### Prerequisites

- Python 3.8+
- YouTube Data API key
- Anthropic API key (Claude)
- Supabase account and credentials

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/youtube_analyzer.git
cd youtube_analyzer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create an `.env` file in the project root with the following variables:
```
YOUTUBE_API_KEY=your_youtube_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Running the Application

### Command-Line Interface
To run the application from the command line:

```bash
python main.py
```

This will start an interactive session where you can analyze YouTube videos and ask questions about the content.

### Streamlit Web Interface
For a more user-friendly experience, you can use the Streamlit web interface:

#### Single-Page Interface
```bash
streamlit run app.py
```

#### Multi-Page Interface (Recommended)
```bash
python run_multipage_app.py
```

This will launch a web application in your default browser with the following features:
- A clean, modern UI for searching YouTube channels
- Visual display of channel statistics
- Easy video selection with filtering options
- Real-time progress tracking for video analysis
- Interactive Q&A interface for analyzed videos
- Multi-channel digest generation
- Comprehensive "About" page with application details

## Usage Guide

Run the main script to start the application:

```bash
python main.py
```

The application will guide you through:
1. Entering a YouTube channel name
2. Selecting videos to analyze
3. Generating and storing analysis reports
4. Querying information about the analyzed videos

## Project Structure

- `src/`: Source code for the application
  - `orchestrator.py`: Main workflow controller
  - `data_retriever.py`: YouTube API interaction
  - `report_generator.py`: Transcript retrieval and analysis
  - `qa_agent.py`: Question answering functionality
  - `vector_store.py`: Vector database for semantic search
  - `vector_db_utils.py`: Utilities for vector database management
- `utils/`: Utility functions and configurations
- `data/`: Temporary storage for downloaded data
- `pages/`: Multipage Streamlit UI components
  - `1_Analyze.py`: Channel and video analysis page
  - `2_Q&A.py`: Question answering interface
  - `3_Digest.py`: Multi-channel digest generation
  - `4_About.py`: Application information
- `Home.py`: Main entry point for multipage Streamlit app
- `docs/`: Documentation files
  - [Installation Guide](docs/installation.md): Detailed setup instructions
  - [User Guide](docs/user_guide.md): How to use the application
  - [API Reference](docs/api_reference.md): Code reference documentation
  - [Design Document](docs/design.md): Architecture overview
  - [Vector Database Guide](docs/vector_database.md): Vector search system

## Documentation

For more detailed documentation, please refer to the [docs directory](docs/). The documentation includes:

- **[Installation Guide](docs/installation.md)**: Step-by-step setup instructions
- **[User Guide](docs/user_guide.md)**: Comprehensive usage instructions
- **[API Reference](docs/api_reference.md)**: Detailed code documentation
- **[Design Document](docs/design.md)**: System architecture and design
- **[Vector Database Guide](docs/vector_database.md)**: How the search system works

## License

MIT License

## Troubleshooting

### API Key Authentication Issues

If you encounter an error like `Error analyzing transcript: Error code: 401 - {'type': 'error', 'error': {'type': 'authentication_error', 'message': 'invalid x-api-key'}}`, this indicates an issue with your Anthropic API key. Follow these steps to resolve it:

1. **Run the provided test script**:
   ```
   python tests/test_anthropic.py
   ```
   This script will verify your Anthropic API key configuration and provide guidance on fixing any issues.

2. **Check your API key format**: Valid Anthropic API keys start with `sk-ant-` followed by a unique identifier. Make sure your key follows this format.

3. **Get a valid API key**:
   - Visit [Anthropic Console](https://console.anthropic.com/) and sign in or create an account
   - Navigate to "API Keys" section
   - Create a new API key if needed
   - Copy the key (you'll only see it once)

4. **Update your .env file**:
   - Open the `.env` file in the project root
   - Replace the existing `ANTHROPIC_API_KEY` value with your new key
   - Save the file

5. **Verify installation**:
   - Make sure you have the Anthropic library installed with the correct version:
   ```
   pip install anthropic==0.3.11
   ```
   - You may need to uninstall any conflicting versions first:
   ```
   pip uninstall -y anthropic
   ```

If you continue to experience issues, make sure your API key is active and hasn't expired. API keys may be deactivated for security reasons if they haven't been used for a long time.

### SSL/TLS Issues

If you encounter SSL connection errors when trying to connect to the Anthropic API, the application includes built-in workarounds that should handle most issues automatically. If you still experience problems:

1. Try using the multipage interface with the cache clearing script:
   ```
   python clear_cache_and_run.py
   ```

2. Check your certificate authorities are up to date.

### UI Display Issues

If you notice formatting issues in the UI where analysis results aren't properly displayed:

1. Navigate to the Q&A tab and see if previously analyzed videos are listed
2. If they're listed but display incorrectly, the application has built-in compatibility for different report formats

For any other issues, please check the logs for specific error messages.
