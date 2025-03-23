from src.vector_store import VectorStore
import time
import json
import os

print("===== Testing YouTube Analyzer Vector Store Components =====")

# Initialize the vector store
print("\n1. Initializing Vector Store...")
vs = VectorStore()
print("   ✓ Vector Store initialized successfully")

# Test the text splitter and chunking
print("\n2. Testing text chunking functionality...")
test_text = "This is a test document. " * 100
start_time = time.time()
chunks = vs.text_splitter.split_text(test_text)
chunk_time = time.time() - start_time
print(f"   ✓ Split text into {len(chunks)} chunks in {chunk_time:.4f} seconds")
print(f"   ✓ First chunk size: {len(chunks[0])} characters")
print(f"   ✓ First chunk preview: {chunks[0][:50]}...")

# Test ChromaDB and FAISS
print("\n3. Testing ChromaDB with FAISS backend...")
# Add test documents
test_docs = [
    "Artificial intelligence and machine learning are transforming industries",
    "Natural language processing enables computers to understand human language",
    "Computer vision systems can identify objects and people in images and videos",
    "Deep learning models are based on artificial neural networks with many layers"
]
test_ids = ["test1", "test2", "test3", "test4"]
test_metadata = [{"category": "ai", "index": i} for i in range(len(test_docs))]

print("   Adding test documents to collection...")
start_time = time.time()
with vs.lock:
    vs.reports_collection.add(
        documents=test_docs,
        ids=test_ids,
        metadatas=test_metadata
    )
add_time = time.time() - start_time
print(f"   ✓ Added {len(test_docs)} documents in {add_time:.4f} seconds")

# Test vector search
print("\n4. Testing vector similarity search...")
test_queries = [
    "artificial intelligence",
    "language understanding",
    "image recognition",
    "neural networks"
]

for query in test_queries:
    start_time = time.time()
    results = vs.reports_collection.query(
        query_texts=[query],
        n_results=2
    )
    search_time = time.time() - start_time

    print(f"\n   Query: '{query}'")
    print(f"   ✓ Found {len(results['documents'][0])} results in {search_time:.4f} seconds")
    for i, doc in enumerate(results['documents'][0]):
        print(f"   - Result {i+1}: {doc}")

# Test caching
print("\n5. Testing disk cache functionality...")
cache_key = vs._get_cache_key("test_text")
print("   Writing to cache...")
start_time = time.time()
vs.cache[cache_key] = "test_value"
write_time = time.time() - start_time

print("   Reading from cache...")
start_time = time.time()
cached_value = vs.cache[cache_key]
read_time = time.time() - start_time

print(f"   ✓ Cache write time: {write_time:.4f} seconds")
print(f"   ✓ Cache read time: {read_time:.4f} seconds")
print(f"   ✓ Cache test successful: {cached_value == 'test_value'}")

# Check ChromaDB persistent storage
print("\n6. Testing ChromaDB persistence...")
vector_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "vector_db")
print(f"   Vector database directory: {vector_dir}")
print(f"   ✓ Directory exists: {os.path.exists(vector_dir)}")
if os.path.exists(vector_dir):
    items = os.listdir(vector_dir)
    print(f"   ✓ Contents: {', '.join(items) if items else 'empty'}")

print("\n===== Testing completed =====")
