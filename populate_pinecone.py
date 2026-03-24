"""Populate Pinecone index with test vectors for the Gilial dashboard."""

import os
import random
from pinecone import Pinecone

# Get API key from environment
API_KEY = os.getenv("PINECONE_API_KEY")
if not API_KEY:
    raise ValueError("PINECONE_API_KEY not set in environment")

# Configuration
INDEX_NAME = input("Enter your Pinecone index name: ").strip()
NUM_VECTORS = int(input("How many test vectors to create? (default 100): ") or "100")
VECTOR_DIMENSION = 1024

print(f"\nConnecting to Pinecone index '{INDEX_NAME}'...")
pc = Pinecone(api_key=API_KEY)
index = pc.Index(INDEX_NAME)

# Generate random vectors with metadata
vectors_to_upsert = []
for i in range(NUM_VECTORS):
    vector_id = f"vector_{i:04d}"
    # Generate random 1024-dimensional vector
    vector_data = [random.uniform(-1, 1) for _ in range(VECTOR_DIMENSION)]
    metadata = {
        "text": f"Memory {i}: Sample conversation context or knowledge",
        "timestamp": 1700000000 + i * 3600,
        "type": random.choice(["conversation", "knowledge", "context"]),
        "layer": random.choice(["short-term", "long-term", "compressed"]),
    }
    vectors_to_upsert.append((vector_id, vector_data, metadata))

print(f"Upserting {NUM_VECTORS} vectors to index...")
index.upsert(vectors=vectors_to_upsert, namespace="default")

print(f"✓ Successfully populated '{INDEX_NAME}' with {NUM_VECTORS} test vectors!")
print(f"\nYou can now:")
print(f"1. Start the backend: cd backend && python main.py")
print(f"2. Start the frontend: cd dashboard && npm run dev")
print(f"3. Open http://localhost:3001 and connect with your API key + index name '{INDEX_NAME}'")
