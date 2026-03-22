from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class RetrievalMetrics:
    ndcg: float
    mrr: float
    k: int


@dataclass
class StorageMetrics:
    memories_before: int
    memories_after: int
    reduction_ratio: float


@dataclass
class FalseDeletionMetrics:
    canary_ids: list[str]
    lost_ids: list[str]
    false_deletion_rate: float


@dataclass
class EvalReport:
    retrieval: RetrievalMetrics
    storage: StorageMetrics
    false_deletion: FalseDeletionMetrics
    coverage_retention: float
    timestamp: str
    passed: bool

    @staticmethod
    def build(
        retrieval: RetrievalMetrics,
        storage: StorageMetrics,
        false_deletion: FalseDeletionMetrics,
        coverage_retention: float,
        ndcg_threshold: float = 0.5,
        coverage_threshold: float = 0.7,
    ) -> EvalReport:
        passed = (
            retrieval.ndcg >= ndcg_threshold
            and false_deletion.false_deletion_rate == 0.0
            and coverage_retention >= coverage_threshold
        )
        return EvalReport(
            retrieval=retrieval,
            storage=storage,
            false_deletion=false_deletion,
            coverage_retention=coverage_retention,
            timestamp=datetime.now(timezone.utc).isoformat(),
            passed=passed,
        )


def compute_ndcg(relevant_ids: list[str], retrieved_ids: list[str], k: int) -> float:
    relevant_set = set(relevant_ids)
    dcg = 0.0
    for i in range(min(k, len(retrieved_ids))):
        rel = 1.0 if retrieved_ids[i] in relevant_set else 0.0
        dcg += rel / math.log2(i + 2)

    ideal_hits = min(k, len(relevant_ids))
    idcg = 0.0
    for i in range(ideal_hits):
        idcg += 1.0 / math.log2(i + 2)

    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def compute_mrr(relevant_ids: list[str], retrieved_ids: list[str]) -> float:
    relevant_set = set(relevant_ids)
    for i, rid in enumerate(retrieved_ids):
        if rid in relevant_set:
            return 1.0 / (i + 1)
    return 0.0
