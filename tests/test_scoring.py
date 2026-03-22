"""Tests for Phase 2 importance scoring."""
import json
import math
import pytest
from datetime import datetime, timezone, timedelta
from gilial.core.schema import Memory
from gilial.scoring.scoring import compute_importance, score_all, _recency_score, _access_score, _retrieval_rank_score


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_memory(access_count=0, importance_score=0.0) -> Memory:
    mem = Memory.create(
        content="test memory",
        embedding=[0.0] * 128,
        tags=[],
        importance_score=importance_score,
    )
    mem.access_count = access_count
    return mem

def write_telemetry(tmp_path, events: list[dict]) -> str:
    path = tmp_path / "telemetry.jsonl"
    with open(path, "w") as f:
        for e in events:
            if "timestamp" not in e:
                e["timestamp"] = datetime.now(timezone.utc).isoformat()
            f.write(json.dumps(e) + "\n")
    return str(path)


# ── 1. Recency score ─────────────────────────────────────────────────────────

def test_recency_score_recent_access():
    """A memory accessed just now should score close to 1.0."""
    events = [{"event": "read", "memory_id": "x", "timestamp": datetime.now(timezone.utc).isoformat()}]
    score = _recency_score(events)
    assert score > 0.99

def test_recency_score_old_access():
    """A memory last accessed 90 days ago should score much lower than one from today."""
    old_time = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    events = [{"event": "read", "memory_id": "x", "timestamp": old_time}]
    score = _recency_score(events)
    assert score < 0.1

def test_recency_score_no_events():
    assert _recency_score([]) == 0.0


# ── 2. Access frequency score ─────────────────────────────────────────────────

def test_access_score_highest_count():
    """The memory with the highest access_count should score 1.0."""
    high = make_memory(access_count=10)
    low = make_memory(access_count=2)
    assert _access_score(high, [high, low]) == 1.0

def test_access_score_zero_count():
    """A never-accessed memory scores 0.0 when others have been accessed."""
    zero = make_memory(access_count=0)
    other = make_memory(access_count=5)
    assert _access_score(zero, [zero, other]) == 0.0

def test_access_score_all_zero():
    """When all memories have zero access_count, score is 0.0."""
    mems = [make_memory(access_count=0) for _ in range(3)]
    assert _access_score(mems[0], mems) == 0.0


# ── 3. Retrieval rank score ───────────────────────────────────────────────────

def test_retrieval_rank_perfect_match():
    """Distance of 0.0 should yield score of 1.0."""
    events = [{"event": "read", "memory_id": "x", "similarity_score": 0.0, "timestamp": datetime.now(timezone.utc).isoformat()}]
    assert _retrieval_rank_score(events) == 1.0

def test_retrieval_rank_no_read_events():
    """No read events returns neutral 0.5."""
    assert _retrieval_rank_score([]) == 0.5

def test_retrieval_rank_averages_multiple():
    """Score is average across multiple read events."""
    events = [
        {"event": "read", "memory_id": "x", "similarity_score": 0.0, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"event": "read", "memory_id": "x", "similarity_score": 2.0, "timestamp": datetime.now(timezone.utc).isoformat()},
    ]
    # (1.0 + 0.0) / 2 = 0.5
    assert abs(_retrieval_rank_score(events) - 0.5) < 1e-9


# ── 4. Composite score ────────────────────────────────────────────────────────

def test_compute_importance_returns_valid_range(tmp_path):
    """Score must always be in [0.0, 1.0]."""
    mem = make_memory(access_count=3)
    tel = write_telemetry(tmp_path, [
        {"event": "write", "memory_id": mem.id},
        {"event": "read", "memory_id": mem.id, "similarity_score": 0.5},
    ])
    score = compute_importance(mem, [mem], telemetry_path=tel)
    assert 0.0 <= score <= 1.0

def test_frequently_accessed_scores_higher(tmp_path):
    """A memory retrieved many times should score higher than one never retrieved."""
    high = make_memory(access_count=20)
    low = make_memory(access_count=0)
    tel = write_telemetry(tmp_path, [
        {"event": "read", "memory_id": high.id, "similarity_score": 0.3},
    ] * 5)
    high_score = compute_importance(high, [high, low], telemetry_path=tel)
    low_score = compute_importance(low, [high, low], telemetry_path=tel)
    assert high_score > low_score


# ── 5. score_all ─────────────────────────────────────────────────────────────

def test_score_all_returns_all_ids(tmp_path):
    mems = [make_memory() for _ in range(5)]
    tel = write_telemetry(tmp_path, [])
    scores = score_all(mems, telemetry_path=tel)
    assert set(scores.keys()) == {m.id for m in mems}

def test_score_all_values_in_range(tmp_path):
    mems = [make_memory(access_count=i) for i in range(5)]
    tel = write_telemetry(tmp_path, [])
    for score in score_all(mems, telemetry_path=tel).values():
        assert 0.0 <= score <= 1.0
