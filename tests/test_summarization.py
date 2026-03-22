"""Tests for Phase 3c LLM-based summarization."""
import json
import math
import pytest
from unittest.mock import MagicMock, patch
from gilial.core.schema import Memory
from gilial.pipeline.summarization import (
    run_summarization,
    _find_summary_groups,
    SummaryGroup,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def unit_vec(index: int, dim: int = 64) -> list[float]:
    v = [0.0] * dim
    v[index % dim] = 1.0
    return v

def scaled_vec(index: int, scale: float, dim: int = 64) -> list[float]:
    """A vector between two unit vectors — controls cosine similarity."""
    v = [0.0] * dim
    v[index % dim] = 1.0
    v[(index + 1) % dim] = scale
    norm = math.sqrt(sum(x*x for x in v))
    return [x / norm for x in v]

def make_memory(embedding: list[float], content: str = "test", importance_score: float = 0.5, access_count: int = 1) -> Memory:
    m = Memory.create(content=content, embedding=embedding, tags=["t"])
    m.importance_score = importance_score
    m.access_count = access_count
    return m

def mock_db():
    db = MagicMock()
    db.delete = MagicMock()
    return db

def mock_writer(stored: list):
    writer = MagicMock()
    def fake_store(content, tags=None, importance_score=0.0):
        m = Memory.create(content=content, embedding=[0.0]*64, tags=tags or [])
        m.importance_score = importance_score
        stored.append(m)
        return m
    writer.store.side_effect = fake_store
    writer.db = mock_db()
    return writer

def fake_llm(texts: list[str]) -> str:
    return "Summary: " + " + ".join(t[:20] for t in texts)


# ── 1. _find_summary_groups ───────────────────────────────────────────────────

def test_find_summary_groups_in_range():
    """Memories with similarity in [0.75, 0.92) should be grouped."""
    # scale=0.4 gives sim ~0.93 — too high; use scale=0.8 for ~0.78
    a = make_memory(scaled_vec(0, 0.8), content="A")
    b = make_memory(unit_vec(0), content="B")
    groups = _find_summary_groups([a, b], low_threshold=0.75, high_threshold=0.92)
    assert len(groups) == 1
    assert len(groups[0].members) == 2

def test_find_summary_groups_too_similar_not_grouped():
    """Memories above high_threshold should NOT be grouped (merging territory)."""
    a = make_memory(scaled_vec(0, 0.01), content="A")  # very close to unit_vec(0)
    b = make_memory(unit_vec(0), content="B")
    groups = _find_summary_groups([a, b], low_threshold=0.75, high_threshold=0.92)
    assert len(groups) == 0

def test_find_summary_groups_too_dissimilar_not_grouped():
    """Orthogonal memories should NOT be grouped."""
    a = make_memory(unit_vec(0), content="A")
    b = make_memory(unit_vec(1), content="B")
    groups = _find_summary_groups([a, b], low_threshold=0.75, high_threshold=0.92)
    assert len(groups) == 0


# ── 2. run_summarization dry_run ──────────────────────────────────────────────

def test_dry_run_does_not_delete_or_store(tmp_path):
    a = make_memory(scaled_vec(0, 0.8), content="Paris is a city in France")
    b = make_memory(unit_vec(0), content="France is a country in Europe")
    db = mock_db()
    stored = []
    writer = mock_writer(stored)
    with patch("gilial.summarization._cluster", return_value={0: [a, b]}):
        result = run_summarization([a, b], db, writer, fake_llm,
                                   low_threshold=0.75, high_threshold=0.92,
                                   dry_run=True, log_path=str(tmp_path/"s.jsonl"))
    db.delete.assert_not_called()
    assert len(stored) == 0
    assert result.dry_run is True

def test_dry_run_still_generates_summary_text(tmp_path):
    """Even in dry run, summary_text should be populated."""
    a = make_memory(scaled_vec(0, 0.8), content="Paris is a city")
    b = make_memory(unit_vec(0), content="France is a country")
    with patch("gilial.summarization._cluster", return_value={0: [a, b]}):
        result = run_summarization([a, b], mock_db(), mock_writer([]), fake_llm,
                                   low_threshold=0.75, high_threshold=0.92,
                                   dry_run=True, log_path=str(tmp_path/"s.jsonl"))
    assert len(result.summary_groups) == 1
    assert result.summary_groups[0].summary_text.startswith("Summary:")


# ── 3. run_summarization real run ─────────────────────────────────────────────

def test_real_run_stores_summary_and_deletes_sources(tmp_path):
    a = make_memory(scaled_vec(0, 0.8), content="A", importance_score=0.7)
    b = make_memory(unit_vec(0), content="B", importance_score=0.5)
    db = mock_db()
    stored = []
    writer = mock_writer(stored)
    with patch("gilial.summarization._cluster", return_value={0: [a, b]}):
        run_summarization([a, b], db, writer, fake_llm,
                          low_threshold=0.75, high_threshold=0.92,
                          dry_run=False, log_path=str(tmp_path/"s.jsonl"))
    assert db.delete.call_count == 2
    assert len(stored) == 1


# ── 4. Metadata preservation ──────────────────────────────────────────────────

def test_summary_takes_max_importance(tmp_path):
    a = make_memory(scaled_vec(0, 0.8), content="A", importance_score=0.9)
    b = make_memory(unit_vec(0), content="B", importance_score=0.3)
    stored = []
    writer = mock_writer(stored)
    with patch("gilial.summarization._cluster", return_value={0: [a, b]}):
        run_summarization([a, b], mock_db(), writer, fake_llm,
                          low_threshold=0.75, high_threshold=0.92,
                          dry_run=False, log_path=str(tmp_path/"s.jsonl"))
    assert stored[0].importance_score == 0.9


# ── 5. Unchanged memories ─────────────────────────────────────────────────────

def test_unchanged_memories_returned(tmp_path):
    a = make_memory(scaled_vec(0, 0.8), content="A")
    b = make_memory(unit_vec(0), content="B")
    far = make_memory(unit_vec(10), content="C")
    with patch("gilial.summarization._cluster", return_value={0: [a, b], -1: [far]}):
        result = run_summarization([a, b, far], mock_db(), mock_writer([]), fake_llm,
                                   low_threshold=0.75, high_threshold=0.92,
                                   dry_run=True, log_path=str(tmp_path/"s.jsonl"))
    assert far in result.unchanged


# ── 6. Log written ────────────────────────────────────────────────────────────

def test_summarization_log_written(tmp_path):
    a = make_memory(scaled_vec(0, 0.8), content="A")
    b = make_memory(unit_vec(0), content="B")
    log = tmp_path / "s.jsonl"
    with patch("gilial.summarization._cluster", return_value={0: [a, b]}):
        run_summarization([a, b], mock_db(), mock_writer([]), fake_llm,
                          low_threshold=0.75, high_threshold=0.92,
                          dry_run=True, log_path=str(log))
    assert log.exists()
    events = [json.loads(l) for l in log.read_text().splitlines()]
    assert events[0]["event"] == "dry_run_summarize"
    assert a.id in events[0]["member_ids"]


# ── 7. Single memory unchanged ────────────────────────────────────────────────

def test_single_memory_unchanged(tmp_path):
    m = make_memory(unit_vec(0))
    result = run_summarization([m], mock_db(), mock_writer([]), fake_llm,
                               dry_run=True, log_path=str(tmp_path/"s.jsonl"))
    assert result.unchanged == [m]
    assert result.summary_groups == []


# ── 8. LLM fn is called with member content ───────────────────────────────────

def test_llm_fn_called_with_member_content(tmp_path):
    a = make_memory(scaled_vec(0, 0.8), content="Content A")
    b = make_memory(unit_vec(0), content="Content B")
    calls = []
    def tracking_llm(texts):
        calls.append(texts)
        return "summary"
    with patch("gilial.summarization._cluster", return_value={0: [a, b]}):
        run_summarization([a, b], mock_db(), mock_writer([]), tracking_llm,
                          low_threshold=0.75, high_threshold=0.92,
                          dry_run=True, log_path=str(tmp_path/"s.jsonl"))
    assert len(calls) == 1
    assert "Content A" in calls[0]
    assert "Content B" in calls[0]
