# Vector Database Guide

This document explains how the vector database works in YouTube Analyzer and how to use it effectively.

## Table of Contents

1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [Vector Database Management](#vector-database-management)
4. [Using the Vector Database](#using-the-vector-database)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Configuration](#advanced-configuration)

## Overview

The YouTube Analyzer uses a vector database to efficiently store and retrieve information from video transcripts and analysis reports. This enables the application to quickly answer user questions by finding the most relevant content from analyzed videos.

Key benefits:
- Fast semantic search across all analyzed videos
- Finds relevant content even when exact keywords aren't used
- Scales efficiently as you analyze more videos
- Optimizes context provided to the AI for better answers

## How It Works

### Embedding Generation

The vector database works by converting text into numerical vectors (embeddings) that capture semantic meaning. The application uses a language model to generate these embeddings, with each piece of text represented as a high-dimensional vector.

When videos are analyzed:
1. The transcript is chunked into manageable segments
2. The analysis report is separated into logical sections
3. Each chunk is converted into an embedding vector
4. These vectors are stored in collections with metadata

### Semantic Search

When you ask a question:
1. Your question is converted into an embedding vector
2. This vector is compared with all stored vectors using cosine similarity
3. The most similar chunks (closest vectors) are retrieved
4. These chunks are used as context for the AI to generate an answer

## Vector Database Management

The application provides a Vector Database Management page where you can:

### View Database Statistics

- **Reports Indexed**: Number of report chunks in the database
- **Transcripts Indexed**: Number of transcript chunks in the database
- **Total Chunks**: Combined total of all chunks

### Perform Maintenance

- **Reindex All Data**: Rebuilds the entire vector database
  - Use this if you've added many new videos or experiencing retrieval issues
  - This process may take several minutes depending on your data size

- **Clear Embedding Cache**: Removes cached embeddings to free space
  - Cached embeddings speed up reindexing but can consume disk space
  - Clearing the cache doesn't affect retrieval quality

- **Fix Incomplete Reports**: Repair reports that were incorrectly generated
  - Identifies reports with errors and attempts to regenerate them
  - Can fix a specific video or search for all problematic reports

### Test Retrieval Quality

The Vector Database page includes a Test Retrieval section where you can:
1. Enter a test query
2. Set the number of results to retrieve
3. Run the query and examine the results
4. See which chunks were retrieved and their relevance scores

This helps you understand how well the vector search is working and troubleshoot any issues.

## Using the Vector Database

### Optimizing Queries

To get the best results when asking questions:

- **Be specific**: Rather than "Tell me about the video," ask "What does the video say about dopamine and exercise?"
- **Use domain terminology**: Include relevant technical terms that might appear in the videos
- **Limit scope when needed**: Use the "Limit question to specific videos" option for targeted queries
- **Reference content type**: Specify if you're looking for examples, statistics, or recommendations

### Understanding Answers

When you receive an answer:
- The AI combines information from the most relevant chunks
- It may synthesize information from multiple videos
- If the answer seems incomplete, try rephrasing your question
- For very specific information, specifying the video can help

## Troubleshooting

### Common Issues

#### Poor Quality Answers

If answers don't seem to match the content you expect:

1. **Try reindexing**: Go to the Vector Database page and click "Reindex All Data"
2. **Check retrieved chunks**: Use the Test Retrieval tool to see what content is being found
3. **Adjust query specificity**: Make your question more specific to target relevant content
4. **Check indexed videos**: Ensure the videos you're asking about have been successfully analyzed

#### Slow Performance

If retrieval is slow:

1. **Check database size**: Large databases (many videos) may be slower
2. **Optimize hardware**: The application performs better with more RAM
3. **Clear cache**: Try clearing the embedding cache and reindexing

#### Missing Content

If answers don't include information you know exists in the videos:

1. **Check chunking**: Very long segments in videos might be split across chunks
2. **Verify analysis**: Ensure the video was completely analyzed (check transcript availability)
3. **Try keyword variations**: The embedding model might respond differently to synonym terms

## Advanced Configuration

Advanced users can modify vector database settings:

### Directory Structure

The vector database files are stored in:
```
data/vector_db/       # Main database directory
│   ├── reports/      # Report embeddings
│   └── transcripts/  # Transcript embeddings
```

### Configuration Options

In `.env` you can configure:

```
# Vector database settings
EMBEDDING_MODEL=all-MiniLM-L6-v2  # The model used for embeddings
VECTOR_DB_DIR=data/vector_db      # Database location
EMBEDDING_CACHE_DIR=data/embedding_cache  # Cache location
CHUNK_SIZE=500                    # Character length for chunking
CHUNK_OVERLAP=50                  # Overlap between chunks
```

### Custom Embeddings

For advanced users who want to experiment with different embedding models:

1. The application uses the Sentence Transformers library for embeddings
2. You can change the model by modifying the `EMBEDDING_MODEL` setting
3. Popular alternatives include:
   - `paraphrase-MiniLM-L3-v2` (faster but less accurate)
   - `all-mpnet-base-v2` (more accurate but slower)

Remember to reindex your database after changing the embedding model.
