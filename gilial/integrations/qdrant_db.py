from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue, SetPayload,
)
from gilial.core.schema import Memory
from datetime import datetime


class QdrantDB:
    def __init__(self, url: str = "http://localhost:6333", collection_name: str = "memories", dimension: int = 1536):
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self.dimension = dimension

        collections = [c.name for c in self.client.get_collections().collections]
        if collection_name not in collections:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )

    def add_memory(self, memory: Memory):
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(
                id=memory.id,
                vector=memory.embedding,
                payload={
                    "content": memory.content,
                    "timestamp": memory.timestamp.isoformat(),
                    "access_count": memory.access_count,
                    "importance_score": memory.importance_score,
                    "tags": memory.tags,
                },
            )],
        )

    def get_by_id(self, id: str) -> Memory | None:
        results = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[id],
            with_vectors=True,
        )
        if not results:
            return None
        return self._to_memory(results[0])

    def update_metadata(self, memory: Memory):
        self.client.set_payload(
            collection_name=self.collection_name,
            payload={
                "content": memory.content,
                "timestamp": memory.timestamp.isoformat(),
                "access_count": memory.access_count,
                "importance_score": memory.importance_score,
                "tags": memory.tags,
            },
            points=[memory.id],
        )

    def get_all(self) -> list[Memory]:
        results = self.client.scroll(
            collection_name=self.collection_name,
            with_vectors=True,
            limit=10000,
        )
        return [self._to_memory(point) for point in results[0]]

    def delete(self, memory_id: str):
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[memory_id],
        )

    def search(self, query_embedding: list[float], n_results: int = 5) -> list[tuple[Memory, float]]:
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=n_results,
            with_vectors=True,
            with_payload=True,
        )
        memories = []
        for point in results.points:
            m = self._to_memory(point)
            memories.append((m, point.score))
        return memories

    def _to_memory(self, point) -> Memory:
        payload = point.payload
        return Memory(
            id=point.id,
            content=payload["content"],
            embedding=point.vector,
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            access_count=int(payload.get("access_count", 0)),
            importance_score=float(payload.get("importance_score", 0.0)),
            tags=payload.get("tags", []),
        )
