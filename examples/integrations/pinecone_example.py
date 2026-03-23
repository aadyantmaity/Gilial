"""Example: Using Gilial with Pinecone as the vector database."""

from gilial.integrations.pinecone import PineconeDB
from gilial.core.schema import Memory

# Initialize with your Pinecone API key
db = PineconeDB(api_key="your-api-key-here", index_name="gilial-memories")

# Create and add a memory
memory = Memory.create(
    content="The user prefers concise responses.",
    embedding=[0.1] * 1536,  # Replace with real embeddings
    tags=["preference", "style"],
    importance_score=0.8,
)
db.add_memory(memory)
print(f"Added memory: {memory.id}")

# Retrieve by ID
retrieved = db.get_by_id(memory.id)
print(f"Retrieved: {retrieved.content}")

# Search by embedding similarity
results = db.search(query_embedding=[0.1] * 1536, n_results=3)
for mem, distance in results:
    print(f"  [{distance:.3f}] {mem.content}")

# Update metadata
memory.access_count += 1
memory.importance_score = 0.9
db.update_metadata(memory)
print("Updated metadata.")

# Get all memories
all_memories = db.get_all()
print(f"Total memories: {len(all_memories)}")

# Delete
db.delete(memory.id)
print("Deleted memory.")
