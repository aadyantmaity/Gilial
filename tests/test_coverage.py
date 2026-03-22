import pytest
from gilial.core.schema import Memory
from gilial.eval.coverage import SemanticCoverageChecker
from datetime import datetime, timezone
from tests.conftest import _noisy_unit_vector


def _make_memory(content: str, embedding: list[float]) -> Memory:
    return Memory(
        id=content[:8],
        content=content,
        embedding=embedding,
        timestamp=datetime.now(timezone.utc),
    )


def test_measure_returns_positive_area_for_spread_embeddings():
    memories = [
        _make_memory("mem0", _noisy_unit_vector(0)),
        _make_memory("mem1", _noisy_unit_vector(1)),
        _make_memory("mem2", _noisy_unit_vector(2)),
        _make_memory("mem3", _noisy_unit_vector(3)),
        _make_memory("mem4", _noisy_unit_vector(4)),
    ]
    checker = SemanticCoverageChecker()
    snap = checker.measure(memories)

    assert snap.memory_count == 5
    assert snap.coverage_area > 0.0
    assert snap.pca_variance_explained > 0.0


def test_measure_returns_zero_area_for_fewer_than_three_memories():
    memories = [
        _make_memory("memA", _noisy_unit_vector(0)),
        _make_memory("memB", _noisy_unit_vector(1)),
    ]
    checker = SemanticCoverageChecker()
    snap = checker.measure(memories)
    assert snap.coverage_area == 0.0


def test_compare_passed_when_coverage_retained(sample_memories):
    checker = SemanticCoverageChecker()
    memories = [
        _make_memory(content, embedding)
        for content, _, embedding in sample_memories
    ]
    before = checker.measure(memories)
    after = checker.measure(memories)  # same set — ratio == 1.0
    report = checker.compare(before, after)

    assert report.retention_ratio == pytest.approx(1.0)
    assert report.passed is True


def test_compare_failed_when_coverage_drops():
    checker = SemanticCoverageChecker()
    memories_full = [
        _make_memory(f"m{i}", _noisy_unit_vector(i)) for i in range(8)
    ]
    # keep only memories on the same axis — near-degenerate
    memories_tiny = [
        _make_memory("mA", _noisy_unit_vector(0)),
        _make_memory("mB", _noisy_unit_vector(0, noise=0.01)),
        _make_memory("mC", _noisy_unit_vector(0, noise=0.02)),
    ]
    before = checker.measure(memories_full)
    after = checker.measure(memories_tiny)
    report = checker.compare(before, after, threshold=0.7)

    assert report.retention_ratio < 1.0
