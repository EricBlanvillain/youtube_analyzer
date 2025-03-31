# YouTube Video Analyzer

This application allows you to analyze YouTube videos, generate summaries, and interact with video content through Q&A.

## Features

- Video content analysis
- Interactive Q&A about video content
- Summary generation
- Multi-page interface for better organization

## Installation

1. Clone the repository:
```bash
git clone https://github.com/EricBlanvillain/youtube_analyzer.git
cd youtube_analyzer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Running the Application

There are two ways to run the application:

1. Using the start script:
```bash
./start.sh
```

2. Running the Python file directly:
```bash
python src/run_multipage_app.py
```

The application will be available at http://localhost:8501

## Project Structure

```
youtube_analyzer/
├── src/
│   ├── pages/           # Streamlit pages
│   │   ├── 1_Analyze.py
│   │   ├── 2_Q&A.py
│   │   ├── 3_Digest.py
│   │   └── 4_About.py
│   ├── Home.py         # Main page
│   ├── data_retriever.py
│   ├── orchestrator.py
│   ├── qa_agent.py
│   ├── report_generator.py
│   ├── vector_store.py
│   └── run_multipage_app.py  # Main application file
├── tests/              # Test files
├── requirements.txt    # Project dependencies
├── start.sh           # Startup script
└── README.md
```

## Environment Variables

Make sure to set up your environment variables in a `.env` file:

```
ANTHROPIC_API_KEY=your_api_key_here
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.
