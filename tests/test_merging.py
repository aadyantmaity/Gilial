"""Tests for Phase 3b cluster-based memory merging."""
import json
import math
import pytest
from unittest.mock import MagicMock, patch
from gilial.core.schema import Memory
from gilial.pipeline.merging import (
    cosine_similarity,
    _find_merge_groups,
    run_merging,
    MergeGroup,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def unit_vec(index: int, dim: int = 64) -> list[float]:
    v = [0.0] * dim
    v[index % dim] = 1.0
    return v

def near_vec(index: int, noise: float = 0.01, dim: int = 64) -> list[float]:
    """A vector very close to unit_vec(index)."""
    v = unit_vec(index, dim)
    v[(index + 1) % dim] = noise
    norm = math.sqrt(sum(x*x for x in v))
    return [x / norm for x in v]

def make_memory(embedding: list[float], content: str = "test", importance_score: float = 0.5, access_count: int = 0) -> Memory:
    m = Memory.create(content=content, embedding=embedding, tags=["t"])
    m.importance_score = importance_score
    m.access_count = access_count
    return m

def mock_db():
    db = MagicMock()
    db.delete = MagicMock()
    return db

def mock_writer(stored_memories: list):
    """Writer that records stored memories and returns them."""
    writer = MagicMock()
    call_count = [0]
    def fake_store(content, tags=None, importance_score=0.0):
        m = Memory.create(content=content, embedding=[0.0]*64, tags=tags or [])
        m.importance_score = importance_score
        stored_memories.append(m)
        return m
    writer.store.side_effect = fake_store
    writer.db = mock_db()
    return writer


# ── 1. cosine_similarity ──────────────────────────────────────────────────────

def test_cosine_similarity_identical():
    v = unit_vec(0)
    assert abs(cosine_similarity(v, v) - 1.0) < 1e-6

def test_cosine_similarity_orthogonal():
    assert abs(cosine_similarity(unit_vec(0), unit_vec(1))) < 1e-6

def test_cosine_similarity_near_duplicate():
    sim = cosine_similarity(unit_vec(0), near_vec(0, noise=0.01))
    assert sim > 0.99


# ── 2. _find_merge_groups ─────────────────────────────────────────────────────

def test_find_merge_groups_near_duplicates():
    a = make_memory(unit_vec(0), content="Paris is the capital of France")
    b = make_memory(near_vec(0, noise=0.01), content="France's capital city is Paris")
    groups = _find_merge_groups([a, b], threshold=0.92)
    assert len(groups) == 1
    assert len(groups[0].members) == 2

def test_find_merge_groups_orthogonal_not_merged():
    a = make_memory(unit_vec(0))
    b = make_memory(unit_vec(1))
    groups = _find_merge_groups([a, b], threshold=0.92)
    assert len(groups) == 0

def test_find_merge_groups_three_near_duplicates():
    a = make_memory(near_vec(0, noise=0.005))
    b = make_memory(near_vec(0, noise=0.008))
    c = make_memory(near_vec(0, noise=0.003))
    groups = _find_merge_groups([a, b, c], threshold=0.92)
    assert len(groups) == 1
    assert len(groups[0].members) == 3


# ── 3. run_merging dry_run ────────────────────────────────────────────────────

def test_dry_run_does_not_delete(tmp_path):
    a = make_memory(unit_vec(0), content="Paris is the capital of France")
    b = make_memory(near_vec(0, noise=0.01), content="France's capital city is Paris")
    db = mock_db()
    stored = []
    writer = mock_writer(stored)
    with patch("gilial.merging._cluster", return_value={0: [a, b]}):
        result = run_merging([a, b], db, writer, similarity_threshold=0.92, dry_run=True, log_path=str(tmp_path/"m.jsonl"))
    db.delete.assert_not_called()
    assert len(stored) == 0  # no new memory stored in dry run


# ── 4. run_merging real run ───────────────────────────────────────────────────

def test_real_run_deletes_originals_and_stores_merged(tmp_path):
    a = make_memory(unit_vec(0), content="Paris is the capital of France", importance_score=0.6)
    b = make_memory(near_vec(0, noise=0.01), content="France's capital city is Paris", importance_score=0.4)
    db = mock_db()
    stored = []
    writer = mock_writer(stored)
    with patch("gilial.merging._cluster", return_value={0: [a, b]}):
        result = run_merging([a, b], db, writer, similarity_threshold=0.92, dry_run=False, log_path=str(tmp_path/"m.jsonl"))
    assert db.delete.call_count == 2
    assert len(stored) == 1  # one merged memory created


# ── 5. Metadata preservation ──────────────────────────────────────────────────

def test_merged_memory_takes_max_importance(tmp_path):
    a = make_memory(unit_vec(0), content="A", importance_score=0.8)
    b = make_memory(near_vec(0, noise=0.01), content="B", importance_score=0.3)
    db = mock_db()
    stored = []
    writer = mock_writer(stored)
    with patch("gilial.merging._cluster", return_value={0: [a, b]}):
        run_merging([a, b], db, writer, similarity_threshold=0.92, dry_run=False, log_path=str(tmp_path/"m.jsonl"))
    assert stored[0].importance_score == 0.8


# ── 6. Unchanged memories not touched ────────────────────────────────────────

def test_unchanged_memories_returned(tmp_path):
    close_a = make_memory(unit_vec(0), content="A")
    close_b = make_memory(near_vec(0, noise=0.01), content="B")
    far = make_memory(unit_vec(5), content="C")
    db = mock_db()
    stored = []
    writer = mock_writer(stored)
    with patch("gilial.merging._cluster", return_value={0: [close_a, close_b], -1: [far]}):
        result = run_merging([close_a, close_b, far], db, writer, similarity_threshold=0.92, dry_run=True, log_path=str(tmp_path/"m.jsonl"))
    assert far in result.unchanged


# ── 7. Merge log written ──────────────────────────────────────────────────────

def test_merge_log_written(tmp_path):
    a = make_memory(unit_vec(0), content="A")
    b = make_memory(near_vec(0, noise=0.01), content="B")
    log = tmp_path / "m.jsonl"
    with patch("gilial.merging._cluster", return_value={0: [a, b]}):
        run_merging([a, b], mock_db(), mock_writer([]), similarity_threshold=0.92, dry_run=True, log_path=str(log))
    assert log.exists()
    events = [json.loads(l) for l in log.read_text().splitlines()]
    assert events[0]["event"] == "dry_run_merge"
    assert a.id in events[0]["member_ids"]


# ── 8. Too few memories skips clustering ──────────────────────────────────────

def test_single_memory_unchanged(tmp_path):
    m = make_memory(unit_vec(0))
    result = run_merging([m], mock_db(), mock_writer([]), dry_run=True, log_path=str(tmp_path/"m.jsonl"))
    assert result.unchanged == [m]
    assert result.merge_groups == []
