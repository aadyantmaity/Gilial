"""
Qdrant integration example for Gilial.

Prerequisites:
  pip install qdrant-client
  # Run Qdrant locally: docker run -p 6333:6333 qdrant/qdrant
"""

from gilial.integrations.qdrant_db import QdrantDB
from gilial.core.schema import Memory

# --- Initialize ---
db = QdrantDB(
    url="http://localhost:6333",
    collection_name="demo_memories",
    vector_size=384,  # matches all-MiniLM-L6-v2
)

# --- Add memories ---
m1 = Memory.create(
    content="Qdrant is a high-performance vector database.",
    embedding=[0.1] * 384,
    tags=["qdrant", "vector-db"],
    importance_score=0.8,
)
db.add_memory(m1)

m2 = Memory.create(
    content="Gilial uses cosine similarity for memory retrieval.",
    embedding=[0.2] * 384,
    tags=["gilial", "retrieval"],
    importance_score=0.6,
)
db.add_memory(m2)
print(f"Added {m1.id} and {m2.id}")

# --- Retrieve by ID ---
fetched = db.get_by_id(m1.id)
print(f"Fetched: {fetched.content}")

# --- Search ---
results = db.search(query_embedding=[0.15] * 384, n_results=2)
for memory, distance in results:
    print(f"  [{distance:.4f}] {memory.content}")

# --- Update metadata ---
m1.access_count += 1
m1.importance_score = 0.95
db.update_metadata(m1)
print(f"Updated {m1.id}: access_count={m1.access_count}")

# --- List all ---
all_memories = db.get_all()
print(f"Total memories: {len(all_memories)}")

# --- Delete ---
db.delete(m2.id)
print(f"Deleted {m2.id}, remaining: {len(db.get_all())}")
