from pinecone import Pinecone, ServerlessSpec
from gilial.core.schema import Memory
from datetime import datetime


class PineconeDB:
    def __init__(self, api_key: str, index_name: str = "memories", dimension: int = 1536):
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.dimension = dimension

        if index_name not in [idx.name for idx in self.pc.list_indexes()]:
            self.pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
        self.index = self.pc.Index(index_name)

    def add_memory(self, memory: Memory):
        self.index.upsert(vectors=[{
            "id": memory.id,
            "values": memory.embedding,
            "metadata": {
                "content": memory.content,
                "timestamp": memory.timestamp.isoformat(),
                "access_count": memory.access_count,
                "importance_score": memory.importance_score,
                "tags": ",".join(memory.tags),
            },
        }])

    def get_by_id(self, id: str) -> Memory | None:
        result = self.index.fetch(ids=[id])
        if id not in result.vectors:
            return None
        vec = result.vectors[id]
        return self._to_memory(vec)

    def update_metadata(self, memory: Memory):
        self.index.update(
            id=memory.id,
            set_metadata={
                "content": memory.content,
                "timestamp": memory.timestamp.isoformat(),
                "access_count": memory.access_count,
                "importance_score": memory.importance_score,
                "tags": ",".join(memory.tags),
            },
        )

    def get_all(self) -> list[Memory]:
        results = []
        for ids_batch in self.index.list():
            if ids_batch:
                fetched = self.index.fetch(ids=ids_batch)
                for vec in fetched.vectors.values():
                    results.append(self._to_memory(vec))
        return results

    def delete(self, memory_id: str):
        self.index.delete(ids=[memory_id])

    def search(self, query_embedding: list[float], n_results: int = 5) -> list[tuple[Memory, float]]:
        result = self.index.query(
            vector=query_embedding,
            top_k=n_results,
            include_values=True,
            include_metadata=True,
        )
        memories = []
        for match in result.matches:
            meta = match.metadata
            m = Memory(
                id=match.id,
                content=meta["content"],
                embedding=match.values,
                timestamp=datetime.fromisoformat(meta["timestamp"]),
                access_count=int(meta.get("access_count", 0)),
                importance_score=float(meta.get("importance_score", 0.0)),
                tags=meta.get("tags", "").split(",") if meta.get("tags") else [],
            )
            memories.append((m, match.score))
        return memories

    def _to_memory(self, vec) -> Memory:
        meta = vec.metadata
        return Memory(
            id=vec.id,
            content=meta["content"],
            embedding=vec.values,
            timestamp=datetime.fromisoformat(meta["timestamp"]),
            access_count=int(meta.get("access_count", 0)),
            importance_score=float(meta.get("importance_score", 0.0)),
            tags=meta.get("tags", "").split(",") if meta.get("tags") else [],
        )
