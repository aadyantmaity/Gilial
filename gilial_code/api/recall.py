"""Recall validation — benchmark top-k overlap before and after compression."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RecallReport:
    """Results from a before/after recall benchmark."""

    k: int
    num_queries: int
    mean_recall: float
    min_recall: float
    max_recall: float
    per_query_recall: list[float] = field(default_factory=list)
    duration_seconds: float = 0.0

    def __str__(self) -> str:
        pct = self.mean_recall * 100
        lines = [
            f"Recall@{self.k} — {self.num_queries} queries",
            f"  mean : {pct:.2f}%",
            f"  min  : {self.min_recall * 100:.2f}%",
            f"  max  : {self.max_recall * 100:.2f}%",
            f"  time : {self.duration_seconds:.1f}s",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "k": self.k,
            "num_queries": self.num_queries,
            "mean_recall": round(self.mean_recall, 6),
            "min_recall": round(self.min_recall, 6),
            "max_recall": round(self.max_recall, 6),
            "duration_seconds": self.duration_seconds,
        }

    @property
    def safe_to_apply(self) -> bool:
        """True when mean recall is at or above 95%."""
        return self.mean_recall >= 0.95


def _query_top_k(index, vector: list[float], k: int, namespace: Optional[str]) -> list[str]:
    """Return ordered list of vector IDs from a single query."""
    result = index.query(
        vector=vector,
        top_k=k,
        namespace=namespace,
        include_values=False,
        include_metadata=False,
    )
    return [m["id"] for m in result.get("matches", [])]


def _sample_query_vectors(connector, n: int) -> list[list[float]]:
    """Pull n vectors from the index to use as query probes."""
    import numpy as np

    stats = connector.get_index_stats()
    dimension = stats.get("dimension", 1536)
    total = stats.get("total_vector_count", 0)

    if total == 0:
        raise ValueError("Index is empty — cannot sample query vectors.")

    vectors: list[list[float]] = []
    seen: set[str] = set()

    # Use random query vectors to retrieve diverse samples from the index
    attempts = 0
    while len(vectors) < n and attempts < n * 3:
        attempts += 1
        probe = np.random.randn(dimension).tolist()
        try:
            results = connector.index.query(
                vector=probe,
                top_k=min(10, n),
                namespace=connector.namespace,
                include_values=True,
                include_metadata=False,
            )
            for match in results.get("matches", []):
                if match["id"] not in seen and match.get("values"):
                    vectors.append(match["values"])
                    seen.add(match["id"])
                    if len(vectors) >= n:
                        break
        except Exception:
            continue

    if not vectors:
        raise RuntimeError("Could not sample any vectors from the index for recall benchmarking.")

    return vectors[:n]


def run_recall_benchmark(
    connector,
    queries: Optional[list[list[float]]] = None,
    n_queries: int = 100,
    k: int = 10,
) -> tuple[dict[int, list[str]], "RecallReport.__class__"]:
    """Run queries and record top-k results. Returns (baseline_results, _run_fn).

    This is called twice — once before compression and once after — via the
    public `validate_recall` helper below. Direct use is not normally needed.
    """
    start = time.monotonic()

    if queries is None:
        queries = _sample_query_vectors(connector, n_queries)

    baseline: dict[int, list[str]] = {}
    for i, q in enumerate(queries):
        baseline[i] = _query_top_k(connector.index, q, k, connector.namespace)

    return baseline, queries, time.monotonic() - start


def compute_recall(
    before: dict[int, list[str]],
    after: dict[int, list[str]],
    k: int,
    query_time_before: float,
    query_time_after: float,
) -> RecallReport:
    """Compare two sets of top-k results and return a RecallReport."""
    per_query: list[float] = []
    for i in before:
        b = set(before[i])
        a = set(after.get(i, []))
        recall = len(b & a) / k if k > 0 else 1.0
        per_query.append(recall)

    if not per_query:
        return RecallReport(k=k, num_queries=0, mean_recall=1.0, min_recall=1.0, max_recall=1.0)

    return RecallReport(
        k=k,
        num_queries=len(per_query),
        mean_recall=sum(per_query) / len(per_query),
        min_recall=min(per_query),
        max_recall=max(per_query),
        per_query_recall=per_query,
        duration_seconds=round(query_time_before + query_time_after, 2),
    )
