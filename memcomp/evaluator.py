from __future__ import annotations

from memcomp.metrics import (
    RetrievalMetrics,
    StorageMetrics,
    FalseDeletionMetrics,
    EvalReport,
    compute_ndcg,
    compute_mrr,
)
from memcomp.coverage import SemanticCoverageChecker


class CompressionEvaluator:
    def __init__(self, writer, canary_set=None, eval_queries: list[dict] = None):
        self._writer = writer
        self._canary_set = canary_set
        self._eval_queries = eval_queries or []

    def run(self, dry_run=True) -> EvalReport:
        checker = SemanticCoverageChecker()

        memories_before = self._writer.db.get_all()
        count_before = len(memories_before)
        coverage_before = checker.measure(memories_before) if len(memories_before) >= 3 else None

        if self._canary_set is not None:
            canary_ids = list(self._canary_set._canary_ids)
        else:
            canary_ids = []

        self._writer.compress_delete(dry_run=dry_run)
        self._writer.compress_merge(dry_run=dry_run)
        self._writer.compress_summarize(dry_run=dry_run)

        memories_after = self._writer.db.get_all()
        count_after = len(memories_after)
        coverage_after = checker.measure(memories_after) if len(memories_after) >= 3 else None

        if coverage_before is not None and coverage_after is not None:
            coverage_report = checker.compare(coverage_before, coverage_after)
            coverage_retention = coverage_report.retention_ratio
        else:
            coverage_retention = 1.0

        if self._eval_queries:
            ndcg_scores = []
            mrr_scores = []
            k = 5
            for eq in self._eval_queries:
                query = eq["query"]
                relevant_ids = eq["relevant_ids"]
                hits = self._writer.retrieve(query, n_results=k)
                retrieved_ids = [m.id for m, _ in hits]
                ndcg_scores.append(compute_ndcg(relevant_ids, retrieved_ids, k))
                mrr_scores.append(compute_mrr(relevant_ids, retrieved_ids))
            avg_ndcg = sum(ndcg_scores) / len(ndcg_scores)
            avg_mrr = sum(mrr_scores) / len(mrr_scores)
            retrieval = RetrievalMetrics(ndcg=avg_ndcg, mrr=avg_mrr, k=k)
        else:
            retrieval = RetrievalMetrics(ndcg=0.5, mrr=0.5, k=5)

        if self._canary_set is not None:
            verification = self._canary_set.verify(self._writer)
            lost_ids = verification.lost
        else:
            lost_ids = []

        false_deletion = FalseDeletionMetrics(
            canary_ids=canary_ids,
            lost_ids=lost_ids,
            false_deletion_rate=len(lost_ids) / len(canary_ids) if canary_ids else 0.0,
        )

        reduction = (count_before - count_after) / count_before if count_before > 0 else 0.0
        storage = StorageMetrics(
            memories_before=count_before,
            memories_after=count_after,
            reduction_ratio=reduction,
        )

        return EvalReport.build(
            retrieval=retrieval,
            storage=storage,
            false_deletion=false_deletion,
            coverage_retention=coverage_retention,
        )

    def baseline(self, queries: list[dict], k: int = 5) -> dict[str, list[str]]:
        result = {}
        for q in queries:
            query_text = q["query"] if isinstance(q, dict) else q
            hits = self._writer.retrieve(query_text, n_results=k)
            result[query_text] = [m.id for m, _ in hits]
        return result
