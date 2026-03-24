"""Pinecone vector database connector for compression pipeline."""

from typing import Optional, List, Dict, Tuple, Any
import numpy as np

try:
    from pinecone import Pinecone
except ImportError:
    Pinecone = None


class PineconeConnector:
    """Connects to a Pinecone index and implements standard database interface."""

    def __init__(
        self,
        api_key: str,
        index_name: str,
        environment: str = "us-west",
        namespace: Optional[str] = None,
    ):
        """Initialize Pinecone connector.

        Args:
            api_key: Pinecone API key
            index_name: Name of the Pinecone index
            environment: Pinecone environment (default: us-west)
            namespace: Optional namespace within the index
        """
        if Pinecone is None:
            raise ImportError("pinecone-client is required. Install with: pip install pinecone-client")

        self.api_key = api_key
        self.index_name = index_name
        self.environment = environment
        self.namespace = namespace

        try:
            pc = Pinecone(api_key=api_key)
            self.index = pc.Index(index_name)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Pinecone index '{index_name}': {e}")

    def get_all(self, limit: int = 100000) -> List[Dict[str, Any]]:
        """Fetch all vectors from the index.

        Args:
            limit: Maximum number of vectors to fetch

        Returns:
            List of vectors with metadata
        """
        try:
            import numpy as np

            # Get index stats to know dimension and total count
            stats = self.get_index_stats()
            dimension = stats.get("dimension", 1536)
            total_count = stats.get("total_vector_count", 0)

            if total_count == 0:
                return []

            results = []
            seen_ids = set()
            page_size = min(100, limit)
            max_attempts = 10  # Try up to 10 random queries

            # Use multiple random query vectors to get diverse results
            for attempt in range(max_attempts):
                if len(results) >= min(limit, total_count):
                    break

                # Generate a random query vector
                random_vector = np.random.randn(dimension).tolist()

                try:
                    query_results = self.index.query(
                        vector=random_vector,
                        top_k=page_size,
                        namespace=self.namespace,
                        include_metadata=True,
                        include_values=True,
                    )

                    matches = query_results.get("matches", [])
                    if not matches:
                        continue

                    # Fetch full vectors (query gives limited data)
                    ids = [m["id"] for m in matches if m["id"] not in seen_ids]
                    if not ids:
                        continue

                    fetched_vectors = self.index.fetch(ids=ids, namespace=self.namespace)

                    for vid, record in fetched_vectors.get("vectors", {}).items():
                        if vid not in seen_ids:
                            results.append({
                                "id": vid,
                                "values": record.get("values", []),
                                "metadata": record.get("metadata", {}),
                            })
                            seen_ids.add(vid)

                except Exception as e:
                    print(f"Warning: Query attempt {attempt + 1} failed: {e}")
                    continue

            print(f"get_all() fetched {len(results)} vectors (total in index: {total_count})")
            return results
        except Exception as e:
            print(f"Error in get_all(): {e}")
            raise RuntimeError(f"Failed to fetch all vectors: {e}")

    def get_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single vector by ID.

        Args:
            memory_id: The vector ID

        Returns:
            Vector data or None if not found
        """
        try:
            result = self.index.fetch(ids=[memory_id], namespace=self.namespace)
            vectors = result.get("vectors", {})
            if memory_id in vectors:
                record = vectors[memory_id]
                return {
                    "id": memory_id,
                    "values": record.get("values", []),
                    "metadata": record.get("metadata", {}),
                }
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to fetch vector {memory_id}: {e}")

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> List[Tuple[str, float]]:
        """Search for similar vectors using cosine similarity.

        Args:
            query_vector: Query vector
            top_k: Number of results to return
            threshold: Minimum similarity score

        Returns:
            List of (id, similarity) tuples sorted by similarity (descending)
        """
        try:
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=self.namespace,
                include_metadata=False,
            )
            matches = []
            for match in results.get("matches", []):
                if match.get("score", 0) >= threshold:
                    matches.append((match["id"], match["score"]))
            return matches
        except Exception as e:
            raise RuntimeError(f"Failed to search index: {e}")

    def add_memory(self, memory_id: str, values: List[float], metadata: Dict = None) -> None:
        """Add or update a vector in the index.

        Args:
            memory_id: Unique identifier
            values: Vector values
            metadata: Optional metadata dictionary
        """
        try:
            self.index.upsert(
                vectors=[(memory_id, values, metadata or {})],
                namespace=self.namespace,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to add vector {memory_id}: {e}")

    def delete(self, memory_id: str) -> None:
        """Delete a vector from the index.

        Args:
            memory_id: ID of vector to delete
        """
        try:
            self.index.delete(ids=[memory_id], namespace=self.namespace)
        except Exception as e:
            raise RuntimeError(f"Failed to delete vector {memory_id}: {e}")

    def update_metadata(self, memory_id: str, metadata: Dict) -> None:
        """Update metadata for a vector.

        Args:
            memory_id: Vector ID
            metadata: New metadata dictionary
        """
        try:
            # Get current vector and re-upsert with updated metadata
            current = self.get_by_id(memory_id)
            if current:
                self.add_memory(memory_id, current["values"], metadata)
        except Exception as e:
            raise RuntimeError(f"Failed to update metadata for {memory_id}: {e}")

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the index.

        Returns:
            Dictionary with index statistics
        """
        try:
            stats = self.index.describe_index_stats()
            total_count = stats.get("total_vector_count", 0)
            dimension = stats.get("dimension", 0)
            namespaces = stats.get("namespaces", {})

            return {
                "total_vector_count": total_count,
                "dimension": dimension,
                "namespaces": namespaces,
                "index_name": self.index_name,
            }
        except Exception as e:
            raise RuntimeError(f"Failed to get index stats: {e}")

    def _paginate_ids(self, limit: int, page_size: int = 100):
        """Helper to paginate through vector IDs."""
        try:
            fetched = 0
            while fetched < limit:
                # Query with dummy vector to get IDs
                results = self.index.query(
                    vector=[0.0] * 1536,  # Placeholder
                    top_k=page_size,
                    namespace=self.namespace,
                    include_metadata=False,
                )
                ids = [m["id"] for m in results.get("matches", [])]
                if not ids:
                    break
                yield ids
                fetched += len(ids)
        except Exception:
            # Fallback if query-based pagination fails
            pass
