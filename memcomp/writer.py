from sentence_transformers import SentenceTransformer
from memcomp.schema import Memory
from memcomp.db import ChromaDB
from memcomp.telemetry import Telemetry

_model = SentenceTransformer("all-MiniLM-L6-v2")  # 384-dim, runs locally, no API key

class MemoryWriter:
    def __init__(self, chroma_path: str = "./chroma_data"):
        self.model = _model
        self.db = ChromaDB(path=chroma_path)
        self.telemetry = Telemetry()

    def embed(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()

    def store(self, content: str, tags: list[str] = None, importance_score: float = 0.0) -> Memory:
        embedding = self.embed(content)
        memory = Memory.create(content=content, embedding=embedding, tags=tags, importance_score=importance_score)
        self.db.add_memory(memory)
        self.telemetry.log_write(memory.id)
        return memory

    def retrieve(self, query: str, n_results: int = 5) -> list[tuple[Memory, float]]:
        query_embedding = self.embed(query)
        results = self.db.search(query_embedding, n_results=n_results)
        for memory, score in results:
            memory.access_count += 1
            self.db.update_metadata(memory)
            self.telemetry.log_read(memory.id, similarity_score=score)
        self.telemetry.log_search(query, results)
        from memcomp.scoring import compute_importance
        all_memories = self.db.get_all()
        for memory, score in results:
            memory.importance_score = compute_importance(memory, all_memories, str(self.telemetry.log_path))
            self.db.update_metadata(memory)
        return results

    def rescore_all(self) -> dict[str, float]:
        """Recompute and persist importance scores for every memory."""
        from memcomp.scoring import score_all
        all_memories = self.db.get_all()
        scores = score_all(all_memories, str(self.telemetry.log_path))
        for memory in all_memories:
            memory.importance_score = scores[memory.id]
            self.db.update_metadata(memory)
        return scores

    def get(self, memory_id: str) -> Memory | None:
        memory = self.db.get_by_id(memory_id)
        if memory:
            self.telemetry.log_read(memory.id)
        return memory
