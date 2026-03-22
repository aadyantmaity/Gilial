import chromadb
from gilial.schema import Memory
from datetime import datetime

class ChromaDB:
    def __init__(self, path: str = "./chroma_data"):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            "memories", metadata={"hnsw:space": "cosine"}
        )

    def add_memory(self, memory: Memory):
        self.collection.add(
            ids=[memory.id],
            embeddings=[memory.embedding],
            metadatas=[memory.to_chroma_metadata()],
            documents=[memory.content],
        )

    def get_by_id(self, id: str) -> Memory | None:
        result = self.collection.get(ids=[id], include=["embeddings", "metadatas", "documents"])
        if not result["ids"]:
            return None
        return self._to_memory(result, 0)

    def update_metadata(self, memory: Memory):
        self.collection.update(ids=[memory.id], metadatas=[memory.to_chroma_metadata()])

    def get_all(self) -> list[Memory]:
        """Fetch every memory in the collection."""
        result = self.collection.get(include=["embeddings", "metadatas", "documents"])
        if not result["ids"]:
            return []
        return [self._to_memory(result, i) for i in range(len(result["ids"]))]

    def delete(self, memory_id: str):
        """Remove a memory from the collection by ID."""
        self.collection.delete(ids=[memory_id])

    def search(self, query_embedding: list[float], n_results: int = 5) -> list[tuple[Memory, float]]:
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["embeddings", "metadatas", "documents", "distances"],
        )
        memories = []
        for i in range(len(result["ids"][0])):
            m = self._to_memory_from_query(result, i)
            distance = result["distances"][0][i]
            memories.append((m, distance))
        return memories

    def _to_memory(self, result, idx) -> Memory:
        meta = result["metadatas"][idx]
        return Memory(
            id=result["ids"][idx],
            content=result["documents"][idx],
            embedding=result["embeddings"][idx],
            timestamp=datetime.fromisoformat(meta["timestamp"]),
            access_count=meta.get("access_count", 0),
            importance_score=meta.get("importance_score", 0.0),
            tags=meta.get("tags", "").split(",") if meta.get("tags") else [],
        )

    def _to_memory_from_query(self, result, idx) -> Memory:
        meta = result["metadatas"][0][idx]
        return Memory(
            id=result["ids"][0][idx],
            content=result["documents"][0][idx],
            embedding=result["embeddings"][0][idx],
            timestamp=datetime.fromisoformat(meta["timestamp"]),
            access_count=meta.get("access_count", 0),
            importance_score=meta.get("importance_score", 0.0),
            tags=meta.get("tags", "").split(",") if meta.get("tags") else [],
        )
