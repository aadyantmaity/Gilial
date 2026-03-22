import json
import pytest
from gilial.regression import RetrievalRegressionTest, save_snapshot, load_snapshot


def test_snapshot_returns_correct_structure(mock_writer):
    mock_writer.store("Python is great for data science")
    mock_writer.store("Rust is fast and memory safe")

    rrt = RetrievalRegressionTest()
    snap = rrt.snapshot(mock_writer, queries=["programming language"], k=2)

    assert "programming language" in snap.results
    assert isinstance(snap.results["programming language"], list)
    assert snap.timestamp is not None


def test_compare_identical_results_score_one(mock_writer):
    mock_writer.store("The Nile is the longest river")
    mock_writer.store("Mount Everest is the tallest mountain")

    rrt = RetrievalRegressionTest()
    snap = rrt.snapshot(mock_writer, queries=["geography"], k=2)
    report = rrt.compare(mock_writer, snap, k=2)

    assert report.per_query["geography"] == pytest.approx(1.0)
    assert report.mean_score == pytest.approx(1.0)
    assert report.passed is True


def test_compare_different_results_score_zero(mock_writer):
    mock_writer.store("Alpha memory")
    mock_writer.store("Beta memory")

    rrt = RetrievalRegressionTest()
    snap = rrt.snapshot(mock_writer, queries=["alpha"], k=1)

    # replace snapshot results with IDs that don't exist
    snap.results["alpha"] = ["nonexistent-id-1"]
    report = rrt.compare(mock_writer, snap, k=1)

    assert report.per_query["alpha"] == pytest.approx(0.0)
    assert report.passed is False


def test_save_load_snapshot_roundtrip(mock_writer, tmp_path):
    mock_writer.store("Memory about rivers")

    rrt = RetrievalRegressionTest()
    snap = rrt.snapshot(mock_writer, queries=["rivers"], k=1)

    path = tmp_path / "snap.json"
    save_snapshot(snap, path)
    loaded = load_snapshot(path)

    assert loaded.queries == snap.queries
    assert loaded.results == snap.results
    assert loaded.timestamp == snap.timestamp
