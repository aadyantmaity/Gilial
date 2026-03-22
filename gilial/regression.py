from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class RegressionSnapshot:
    queries: list[str]
    results: dict[str, list[str]]  # query -> list of memory IDs
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class RegressionReport:
    per_query: dict[str, float]  # query -> Jaccard score
    mean_score: float
    threshold: float
    passed: bool


class RetrievalRegressionTest:
    def snapshot(self, writer, queries: list[str], k: int = 5) -> RegressionSnapshot:
        results = {}
        for q in queries:
            hits = writer.retrieve(q, n_results=k)
            results[q] = [m.id for m, _ in hits]
        return RegressionSnapshot(queries=queries, results=results)

    def compare(
        self, writer, snapshot: RegressionSnapshot, k: int = 5, threshold: float = 0.8
    ) -> RegressionReport:
        per_query: dict[str, float] = {}
        for q in snapshot.queries:
            before = set(snapshot.results.get(q, []))
            after_hits = writer.retrieve(q, n_results=k)
            after = {m.id for m, _ in after_hits}
            if not before and not after:
                per_query[q] = 1.0
            else:
                intersection = len(before & after)
                union = len(before | after)
                per_query[q] = intersection / union if union > 0 else 1.0
        mean_score = sum(per_query.values()) / len(per_query) if per_query else 1.0
        return RegressionReport(
            per_query=per_query,
            mean_score=mean_score,
            threshold=threshold,
            passed=mean_score >= threshold,
        )


def save_snapshot(snapshot: RegressionSnapshot, path: str | Path):
    with open(path, "w") as f:
        json.dump(
            {"queries": snapshot.queries, "results": snapshot.results, "timestamp": snapshot.timestamp},
            f,
        )


def load_snapshot(path: str | Path) -> RegressionSnapshot:
    with open(path) as f:
        data = json.load(f)
    return RegressionSnapshot(
        queries=data["queries"],
        results=data["results"],
        timestamp=data["timestamp"],
    )
