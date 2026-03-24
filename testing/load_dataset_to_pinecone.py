"""Load Wikipedia dataset to Pinecone index for testing."""

from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import os

# Configuration
API_KEY = os.getenv("PINECONE_API_KEY", "your-api-key")
INDEX_NAME = os.getenv("PINECONE_INDEX", "your-index-name")
BATCH_SIZE = 32
NUM_DOCS = 10000  # Limit to 10000 docs for testing

def load_and_embed():
    """Load Wikipedia dataset and embed to Pinecone."""

    # Initialize embedding model
    print("Loading embedding model...")
    model = SentenceTransformer('all-mpnet-base-v2')  # 768-dim vectors

    # Initialize Pinecone
    print(f"Connecting to Pinecone index: {INDEX_NAME}")
    pc = Pinecone(api_key=API_KEY)
    index = pc.Index(INDEX_NAME)

    # Load Wikipedia dataset
    print("Loading Wikipedia dataset (streaming)...")
    dataset = load_dataset("wikipedia", "20220301.en", split="train", streaming=True)

    # Process and upsert in batches
    vectors_batch = []
    doc_count = 0

    for record in dataset:
        if doc_count >= NUM_DOCS:
            break

        try:
            text = record.get('text', '')
            if not text or len(text.strip()) < 10:
                continue

            # Embed the text
            embedding = model.encode(text).tolist()

            vectors_batch.append((
                f"wiki-{doc_count}",
                embedding,
                {
                    "title": record.get('title', 'unknown'),
                    "source": "wikipedia",
                    "doc_id": doc_count
                }
            ))

            doc_count += 1

            # Upsert when batch is full
            if len(vectors_batch) == BATCH_SIZE:
                index.upsert(vectors=vectors_batch)
                vectors_batch = []

        except Exception as e:
            print(f"Warning: Failed to process document: {e}")
            continue

    # Upsert remaining vectors
    if vectors_batch:
        index.upsert(vectors=vectors_batch)
        print(f"✓ Upserted final batch")

    # Print index stats
    stats = index.describe_index_stats()
    print(f"\nIndex stats:")
    print(f"  Total vectors: {stats.get('total_vector_count', 0)}")
    print(f"  Dimension: {stats.get('dimension', 0)}")
    print(f"  Namespaces: {stats.get('namespaces', {})}")

    print(f"\n✓ Successfully loaded {doc_count} documents to Pinecone!")

if __name__ == "__main__":
    load_and_embed()
