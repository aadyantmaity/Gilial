import pytest
from gilial.eval.audit import CompressionAudit


def test_diff_identifies_deleted_added_retained(mock_writer):
    m1 = mock_writer.store("Memory one")
    m2 = mock_writer.store("Memory two")
    m3 = mock_writer.store("Memory three")

    before_ids = [m1.id, m2.id, m3.id]

    # simulate compression: delete m1, add new summary, keep m2 and m3
    mock_writer.db.delete(m1.id)
    m4 = mock_writer.store("Summary of memory one and something new")
    after_ids = [m2.id, m3.id, m4.id]

    audit = CompressionAudit()
    diff = audit.diff(before_ids, after_ids, mock_writer)

    assert m2.id in [m.id for m in diff.retained_memories]
    assert m3.id in [m.id for m in diff.retained_memories]
    assert m4.id in [m.id for m in diff.added_memories]
    assert "1 deleted" in diff.summary
    assert "1 added" in diff.summary
    assert "2 retained" in diff.summary


def test_format_diff_returns_non_empty_string(mock_writer):
    m1 = mock_writer.store("Alpha fact about the world")
    m2 = mock_writer.store("Beta fact about science")

    before_ids = [m1.id, m2.id]
    mock_writer.db.delete(m1.id)
    after_ids = [m2.id]

    audit = CompressionAudit()
    diff = audit.diff(before_ids, after_ids, mock_writer)
    formatted = audit.format_diff(diff)

    assert len(formatted) > 0
    assert "RETAINED" in formatted
    assert "Compression Diff" in formatted


def test_format_diff_truncates_long_content(mock_writer):
    long_content = "x" * 200
    m = mock_writer.store(long_content)
    before_ids = [m.id]
    after_ids = []

    audit = CompressionAudit()
    diff = audit.diff(before_ids, after_ids, mock_writer)
    formatted = audit.format_diff(diff)

    assert "…" in formatted
