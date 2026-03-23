from pinecone import Pinecone, ServerlessSpec
from gilial.core.schema import Memory
from datetime import datetime


class PineconeDB:
    def __init__(self, api_key: str, index_name: str = "memories", dimension: int = 1536, cloud: str = "aws", region: str = "us-east-1"):
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.dimension = dimension

        if index_name not in [idx.name for idx in self.pc.list_indexes()]:
            self.pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud=cloud, region=region),
            )

        self.index = self.pc.Index(index_name)

    def add_memory(self, memory: Memory):
        self.index.upsert(vectors=[self._to_pinecone_vector(memory)])

    def get_by_id(self, id: str) -> Memory | None:
        result = self.index.fetch(ids=[id])
        if id not in result.vectors:
            return None
        return self._from_pinecone_vector(result.vectors[id])

    def update_metadata(self, memory: Memory):
        self.index.update(
            id=memory.id,
            set_metadata=self._to_pinecone_metadata(memory),
        )

    def get_all(self) -> list[Memory]:
        """Fetch all memories using a zero-vector query with a large top_k."""
        results = self.index.query(
            vector=[0.0] * self.dimension,
            top_k=10000,
            include_values=True,
            include_metadata=True,
        )
        return [self._from_pinecone_match(match) for match in results.matches]

    def delete(self, memory_id: str):
        self.index.delete(ids=[memory_id])

    def search(self, query_embedding: list[float], n_results: int = 5) -> list[tuple[Memory, float]]:
        results = self.index.query(
            vector=query_embedding,
            top_k=n_results,
            include_values=True,
            include_metadata=True,
        )
        return [
            (self._from_pinecone_match(match), 1.0 - match.score)
            for match in results.matches
        ]

    def _to_pinecone_metadata(self, memory: Memory) -> dict:
        return {
            "content": memory.content,
            "timestamp": memory.timestamp.isoformat(),
            "access_count": memory.access_count,
            "importance_score": memory.importance_score,
            "tags": ",".join(memory.tags),
        }

    def _to_pinecone_vector(self, memory: Memory) -> dict:
        return {
            "id": memory.id,
            "values": memory.embedding,
            "metadata": self._to_pinecone_metadata(memory),
        }

    def _from_pinecone_vector(self, vector) -> Memory:
        meta = vector.metadata
        return Memory(
            id=vector.id,
            content=meta["content"],
            embedding=vector.values,
            timestamp=datetime.fromisoformat(meta["timestamp"]),
            access_count=meta.get("access_count", 0),
            importance_score=meta.get("importance_score", 0.0),
            tags=meta.get("tags", "").split(",") if meta.get("tags") else [],
        )

    def _from_pinecone_match(self, match) -> Memory:
        meta = match.metadata
        return Memory(
            id=match.id,
            content=meta["content"],
            embedding=match.values,
            timestamp=datetime.fromisoformat(meta["timestamp"]),
            access_count=meta.get("access_count", 0),
            importance_score=meta.get("importance_score", 0.0),
            tags=meta.get("tags", "").split(",") if meta.get("tags") else [],
        )
