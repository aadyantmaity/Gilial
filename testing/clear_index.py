"""Clear all vectors from a Pinecone index without deleting the index."""

import os
from pinecone import Pinecone

api_key = os.getenv("PINECONE_API_KEY")
index_name = os.getenv("PINECONE_INDEX")

if not api_key or not index_name:
    print("Error: Set PINECONE_API_KEY and PINECONE_INDEX env vars")
    exit(1)

pc = Pinecone(api_key=api_key)
index = pc.Index(index_name)

print(f"Clearing all vectors from index: {index_name}...")
index.delete(delete_all=True)

# Verify
stats = index.describe_index_stats()
total_vectors = stats.get('total_vector_count', 0)
print(f"\n✓ Index cleared!")
print(f"  Index name: {index_name}")
print(f"  Total vectors: {total_vectors}")
print(f"  Dimension: {stats.get('dimension', 0)}")
