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

    def compress_delete(
        self,
        score_floor: float = 0.2,
        protect_top_pct: float = 0.2,
        dry_run: bool = True,
    ) -> "DeletionResult":
        """Run Phase 3a deletion compression. Dry-run by default."""
        from memcomp.deletion import run_deletion, DeletionResult
        all_memories = self.db.get_all()
        # ensure scores are fresh
        scores = self.rescore_all()
        for m in all_memories:
            m.importance_score = scores[m.id]
        return run_deletion(
            memories=all_memories,
            db=self.db,
            score_floor=score_floor,
            protect_top_pct=protect_top_pct,
            dry_run=dry_run,
        )

    def compress_merge(
        self,
        similarity_threshold: float = 0.92,
        min_cluster_size: int = 2,
        dry_run: bool = True,
    ) -> "MergingResult":
        """Run Phase 3b merge compression. Dry-run by default."""
        from memcomp.merging import run_merging, MergingResult
        all_memories = self.db.get_all()
        return run_merging(
            memories=all_memories,
            db=self.db,
            writer=self,
            similarity_threshold=similarity_threshold,
            min_cluster_size=min_cluster_size,
            dry_run=dry_run,
        )

    def get(self, memory_id: str) -> Memory | None:
        memory = self.db.get_by_id(memory_id)
        if memory:
            self.telemetry.log_read(memory.id)
        return memory
