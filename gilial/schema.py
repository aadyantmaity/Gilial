from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid

@dataclass
class Memory:
    id: str
    content: str
    embedding: list[float]
    timestamp: datetime
    access_count: int = 0
    importance_score: float = 0.0
    tags: list[str] = field(default_factory=list)

    @staticmethod
    def create(content: str, embedding: list[float], tags: list[str] = None, importance_score: float = 0.0) -> "Memory":
        return Memory(
            id=str(uuid.uuid4()),
            content=content,
            embedding=embedding,
            timestamp=datetime.now(timezone.utc),
            tags=tags or [],
            importance_score=importance_score,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "embedding": self.embedding,
            "timestamp": self.timestamp.isoformat(),
            "access_count": self.access_count,
            "importance_score": self.importance_score,
            "tags": self.tags,
        }

    @staticmethod
    def from_dict(d: dict) -> "Memory":
        return Memory(
            id=d["id"],
            content=d["content"],
            embedding=d["embedding"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            access_count=d.get("access_count", 0),
            importance_score=d.get("importance_score", 0.0),
            tags=d.get("tags", []),
        )

    def to_chroma_metadata(self) -> dict:
        return {
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "access_count": self.access_count,
            "importance_score": self.importance_score,
            "tags": ",".join(self.tags),
        }
