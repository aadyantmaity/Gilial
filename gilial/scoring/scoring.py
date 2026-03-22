import json
import math
from datetime import datetime, timezone
from pathlib import Path

from gilial.core.schema import Memory


def compute_importance(
    memory: Memory,
    all_memories: list[Memory],
    telemetry_path: str = "./telemetry.jsonl",
) -> float:
    """
    Returns a score in [0.0, 1.0]. Higher = more important.
    """
    events = _load_events(telemetry_path, memory.id)

    recency = _recency_score(events)             # 0-1
    access = _access_score(memory, all_memories)  # 0-1, normalized
    rank = _retrieval_rank_score(events)          # 0-1, from similarity scores
    uniqueness = 0.5                              # placeholder

    return 0.25 * recency + 0.30 * access + 0.20 * rank + 0.25 * uniqueness


def _load_events(telemetry_path: str, memory_id: str) -> list[dict]:
    """Return all telemetry events for this memory_id."""
    path = Path(telemetry_path)
    if not path.exists():
        return []
    events = []
    for line in path.read_text().splitlines():
        e = json.loads(line)
        if e.get("memory_id") == memory_id:
            events.append(e)
    return events


def _recency_score(events: list[dict]) -> float:
    """Exponential decay: score = e^(-days_since_last_access / 30).
    If never accessed, use write time. Returns 0 if no events at all."""
    if not events:
        return 0.0
    def _ensure_aware(dt: datetime) -> datetime:
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
    timestamps = [_ensure_aware(datetime.fromisoformat(e["timestamp"])) for e in events]
    last = max(timestamps)
    now = datetime.now(timezone.utc)
    days = (now - last).total_seconds() / 86400
    return math.exp(-days / 30)


def _access_score(memory: Memory, all_memories: list[Memory]) -> float:
    """Normalize this memory's access_count against the max in the store."""
    max_count = max((m.access_count for m in all_memories), default=1)
    if max_count == 0:
        return 0.0
    return memory.access_count / max_count


def _retrieval_rank_score(events: list[dict]) -> float:
    """Average similarity score from read events (lower distance = higher score).
    Converts cosine distance [0,2] to a score in [0,1]: score = 1 - distance/2.
    Returns 0.5 if no read events with a similarity_score."""
    read_events = [
        e for e in events
        if e.get("event") == "read" and e.get("similarity_score") is not None
    ]
    if not read_events:
        return 0.5  # neutral -- no retrieval data yet
    scores = [1.0 - (e["similarity_score"] / 2.0) for e in read_events]
    return sum(scores) / len(scores)


def score_all(
    memories: list[Memory],
    telemetry_path: str = "./telemetry.jsonl",
) -> dict[str, float]:
    """Return {memory_id: importance_score} for all memories."""
    return {
        m.id: compute_importance(m, memories, telemetry_path)
        for m in memories
    }
