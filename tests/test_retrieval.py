"""Baseline retrieval-quality tests for the Agent Memory Compression System.

These tests run against a mocked OpenAI embedding backend so no real API key
is needed.  Each test uses an isolated temporary Chroma directory via the
``tmp_path`` pytest fixture.
"""

import json
import math
from pathlib import Path

from tests.conftest import _unit_vector, _noisy_unit_vector, EMBED_DIM


# ── 1. Store and retrieve by ID ──────────────────────────────────────────

def test_store_and_retrieve_by_id(mock_writer):
    memory = mock_writer.store("Hello, world!", tags=["greeting"])
    fetched = mock_writer.get(memory.id)
    assert fetched is not None
    assert fetched.id == memory.id
    assert fetched.content == "Hello, world!"
    assert "greeting" in fetched.tags


# ── 2. Search returns closest match ──────────────────────────────────────

def test_search_returns_closest_match(mock_writer, embedding_dispatcher):
    # Register three orthogonal embeddings
    embedding_dispatcher.register("mem-A", _unit_vector(0))
    embedding_dispatcher.register("mem-B", _unit_vector(1))
    embedding_dispatcher.register("mem-C", _unit_vector(2))

    mock_writer.store("mem-A", tags=["a"])
    mock_writer.store("mem-B", tags=["b"])
    mock_writer.store("mem-C", tags=["c"])

    # Query is very close to mem-A
    query_text = "query-near-A"
    embedding_dispatcher.register(query_text, _noisy_unit_vector(0, noise=0.01))

    results = mock_writer.retrieve(query_text, n_results=3)
    assert len(results) >= 1
    assert results[0][0].content == "mem-A"


# ── 3. Search ranking order ──────────────────────────────────────────────

def test_search_ranking_order(mock_writer, embedding_dispatcher):
    # Store 5 memories on successive axes
    for i in range(5):
        name = f"item-{i}"
        embedding_dispatcher.register(name, _unit_vector(i))
        mock_writer.store(name, tags=[f"t{i}"])

    # Query is exactly axis-2
    embedding_dispatcher.register("query-axis2", _unit_vector(2))
    results = mock_writer.retrieve("query-axis2", n_results=5)

    distances = [d for _, d in results]
    assert distances == sorted(distances), (
        f"Results not in ascending distance order: {distances}"
    )
    assert results[0][0].content == "item-2"


# ── 4. Access count increments ───────────────────────────────────────────

def test_access_count_increments(mock_writer, embedding_dispatcher):
    embedding_dispatcher.register("counter-mem", _unit_vector(0))
    mem = mock_writer.store("counter-mem", tags=["count"])

    embedding_dispatcher.register("counter-query", _noisy_unit_vector(0, noise=0.01))
    mock_writer.retrieve("counter-query", n_results=1)
    mock_writer.retrieve("counter-query", n_results=1)

    fetched = mock_writer.get(mem.id)
    assert fetched is not None
    assert fetched.access_count == 2


# ── 5. Telemetry logs written ────────────────────────────────────────────

def test_telemetry_logs_written(mock_writer, tmp_path):
    mock_writer.store("tel-memory", tags=["tel"])

    embedding_dispatcher_query = "tel-memory"  # same text -> same embedding
    mock_writer.retrieve(embedding_dispatcher_query, n_results=1)

    telemetry_file = tmp_path / "telemetry.jsonl"
    assert telemetry_file.exists(), "telemetry.jsonl was not created"

    events = [json.loads(line) for line in telemetry_file.read_text().splitlines()]
    event_types = [e["event"] for e in events]

    assert "write" in event_types, "Expected a 'write' telemetry event"
    assert "read" in event_types, "Expected a 'read' telemetry event"
    assert "search" in event_types, "Expected a 'search' telemetry event"


# ── 6. Retrieval quality baseline (regression anchor) ────────────────────

def test_retrieval_quality_baseline(
    mock_writer, embedding_dispatcher, sample_memories, cluster_queries
):
    """Store 10 memories across 3 topic clusters, then verify that the top
    result for each topic query belongs to the correct cluster.

    This test prints a baseline report so future compression work can be
    compared against it.
    """
    # Register and store all sample memories
    for content, tags, emb in sample_memories:
        embedding_dispatcher.register(content, emb)
        mock_writer.store(content, tags=tags)

    report_lines = ["\n=== Retrieval Quality Baseline Report ===\n"]
    all_passed = True

    for topic, query_emb in cluster_queries.items():
        query_text = f"query-{topic}"
        embedding_dispatcher.register(query_text, query_emb)

        results = mock_writer.retrieve(query_text, n_results=3)

        report_lines.append(f"--- Topic: {topic} ---")
        for rank, (mem, dist) in enumerate(results, 1):
            tag_str = ",".join(mem.tags)
            report_lines.append(
                f"  #{rank}  dist={dist:.4f}  tags=[{tag_str}]  "
                f'"{mem.content[:60]}..."'
            )

        # The top result must belong to the queried cluster
        top_tags = results[0][0].tags
        if topic not in top_tags:
            all_passed = False
            report_lines.append(f"  ** FAIL: top result tags {top_tags} do not contain '{topic}'")
        else:
            report_lines.append(f"  PASS: top result is in '{topic}' cluster")

        report_lines.append("")

    report = "\n".join(report_lines)
    print(report)

    assert all_passed, f"Retrieval quality baseline failed:\n{report}"
