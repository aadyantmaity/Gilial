import pytest
from memcomp.canary import CanarySet


def test_inject_stores_memories_and_returns_ids(mock_writer):
    cs = CanarySet()
    canaries = [
        {"content": "The user's name is Alice"},
        {"content": "The user's goal is to learn Python"},
    ]
    ids = cs.inject(mock_writer, canaries)
    assert len(ids) == 2
    all_ids = {m.id for m in mock_writer.db.get_all()}
    for cid in ids:
        assert cid in all_ids


def test_inject_adds_canary_tag(mock_writer):
    cs = CanarySet()
    cs.inject(mock_writer, [{"content": "Important fact"}])
    memories = mock_writer.db.get_all()
    assert any("canary" in m.tags for m in memories)


def test_verify_passed_when_all_survive(mock_writer):
    cs = CanarySet()
    cs.inject(mock_writer, [{"content": "Canary A"}, {"content": "Canary B"}])
    result = cs.verify(mock_writer)
    assert result.passed is True
    assert result.survival_rate == 1.0
    assert result.lost == []


def test_verify_failed_when_memory_deleted(mock_writer):
    cs = CanarySet()
    ids = cs.inject(mock_writer, [{"content": "Canary X"}, {"content": "Canary Y"}])
    mock_writer.db.delete(ids[0])
    result = cs.verify(mock_writer)
    assert result.passed is False
    assert ids[0] in result.lost
    assert ids[1] in result.survived
    assert result.survival_rate == pytest.approx(0.5)
