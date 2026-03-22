"""Tests for Phase 3a threshold-based deletion."""
import json
import pytest
from unittest.mock import MagicMock
from gilial.schema import Memory
from gilial.deletion import run_deletion, DeletionResult


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_memory(importance_score: float, access_count: int = 0) -> Memory:
    m = Memory.create(content=f"memory with score {importance_score}", embedding=[0.0]*128, tags=[])
    m.importance_score = importance_score
    m.access_count = access_count
    return m

def mock_db():
    db = MagicMock()
    db.delete = MagicMock()
    return db


# ── 1. Dry run does not call db.delete ───────────────────────────────────────

def test_dry_run_does_not_delete(tmp_path):
    memories = [make_memory(0.05), make_memory(0.9)]
    db = mock_db()
    result = run_deletion(memories, db, score_floor=0.2, protect_top_pct=0.1, dry_run=True, log_path=str(tmp_path/"del.jsonl"))
    db.delete.assert_not_called()
    assert result.dry_run is True


# ── 2. Real run calls db.delete for low-score memories ───────────────────────

def test_real_run_deletes_low_scores(tmp_path):
    low = make_memory(0.05)
    high = make_memory(0.9)
    db = mock_db()
    result = run_deletion([low, high], db, score_floor=0.2, protect_top_pct=0.1, dry_run=False, log_path=str(tmp_path/"del.jsonl"))
    db.delete.assert_called_once_with(low.id)
    assert low in result.deleted
    assert high not in result.deleted


# ── 3. Top-N% safeguard always protects highest-scored memories ───────────────

def test_top_pct_always_protected(tmp_path):
    # 5 memories, protect top 20% = top 1
    memories = [make_memory(s) for s in [0.9, 0.05, 0.05, 0.05, 0.05]]
    db = mock_db()
    result = run_deletion(memories, db, score_floor=0.2, protect_top_pct=0.2, dry_run=False, log_path=str(tmp_path/"del.jsonl"))
    top = max(memories, key=lambda m: m.importance_score)
    assert top in result.protected
    assert top not in result.deleted


# ── 4. Memories above score_floor are kept ───────────────────────────────────

def test_memories_above_floor_kept(tmp_path):
    above = make_memory(0.8)
    below = make_memory(0.1)
    db = mock_db()
    result = run_deletion([above, below], db, score_floor=0.5, protect_top_pct=0.1, dry_run=False, log_path=str(tmp_path/"del.jsonl"))
    assert above in result.kept or above in result.protected
    assert below in result.deleted


# ── 5. Empty store returns empty result ──────────────────────────────────────

def test_empty_memories(tmp_path):
    db = mock_db()
    result = run_deletion([], db, dry_run=True, log_path=str(tmp_path/"del.jsonl"))
    assert result.deleted == []
    assert result.protected == []
    assert result.kept == []


# ── 6. Deletion log written correctly ────────────────────────────────────────

def test_deletion_log_written(tmp_path):
    low = make_memory(0.05)
    high = make_memory(0.9)
    log = tmp_path / "del.jsonl"
    run_deletion([low, high], mock_db(), score_floor=0.2, protect_top_pct=0.1, dry_run=True, log_path=str(log))
    assert log.exists()
    events = [json.loads(l) for l in log.read_text().splitlines()]
    assert any(e["memory_id"] == low.id for e in events)
    assert all(e["event"] == "dry_run_delete" for e in events)


# ── 7. summary() output contains key info ────────────────────────────────────

def test_summary_contains_counts(tmp_path):
    memories = [make_memory(s) for s in [0.9, 0.5, 0.1]]
    db = mock_db()
    result = run_deletion(memories, db, score_floor=0.2, protect_top_pct=0.2, dry_run=True, log_path=str(tmp_path/"del.jsonl"))
    summary = result.summary()
    assert "Deleted" in summary
    assert "Protected" in summary
    assert "DRY RUN" in summary


# ── 8. All memories accounted for ────────────────────────────────────────────

def test_no_memory_lost(tmp_path):
    memories = [make_memory(s) for s in [0.9, 0.6, 0.3, 0.1, 0.05]]
    db = mock_db()
    result = run_deletion(memories, db, score_floor=0.25, protect_top_pct=0.2, dry_run=True, log_path=str(tmp_path/"del.jsonl"))
    total = len(result.deleted) + len(result.protected) + len(result.kept)
    assert total == len(memories)
