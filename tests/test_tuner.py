from gilial.tuning.tuner import CompressionTuner, TuneConfig, TuneResult
from gilial.eval.metrics import (
    EvalReport,
    RetrievalMetrics,
    StorageMetrics,
    FalseDeletionMetrics,
)


def _make_report(ndcg=0.8, reduction=0.3, fd_rate=0.0, coverage=0.9):
    return EvalReport(
        retrieval=RetrievalMetrics(ndcg=ndcg, mrr=0.7, k=5),
        storage=StorageMetrics(memories_before=10, memories_after=int(10 * (1 - reduction)), reduction_ratio=reduction),
        false_deletion=FalseDeletionMetrics(canary_ids=[], lost_ids=[], false_deletion_rate=fd_rate),
        coverage_retention=coverage,
        timestamp="2026-01-01T00:00:00+00:00",
        passed=ndcg >= 0.5 and fd_rate == 0.0 and coverage >= 0.7,
    )


class TestCompressionTuner:
    def test_add_config_registers(self):
        tuner = CompressionTuner()
        tuner.add_config("default", TuneConfig())
        tuner.add_config("aggressive", TuneConfig(score_floor=0.4))
        assert len(tuner._configs) == 2

    def test_run_all_returns_one_per_config(self, mock_writer, sample_memories, embedding_dispatcher):
        for content, tags, emb in sample_memories:
            embedding_dispatcher.register(content, emb)
            mock_writer.store(content, tags=tags)

        tuner = CompressionTuner()
        tuner.add_config("default", TuneConfig())
        tuner.add_config("aggressive", TuneConfig(score_floor=0.5))
        results = tuner.run_all(mock_writer, dry_run=True)

        assert len(results) == 2
        assert all(isinstance(r, TuneResult) for r in results)

    def test_best_aggressive_returns_highest_reduction(self):
        tuner = CompressionTuner()
        results = [
            TuneResult(config=TuneConfig(), report=_make_report(reduction=0.2), label="low"),
            TuneResult(config=TuneConfig(score_floor=0.5), report=_make_report(reduction=0.6), label="high"),
        ]
        best = tuner.best(results, prefer="aggressive")
        assert best.label == "high"

    def test_summary_table_returns_nonempty_string(self):
        tuner = CompressionTuner()
        results = [
            TuneResult(config=TuneConfig(), report=_make_report(), label="default"),
        ]
        table = tuner.summary_table(results)
        assert isinstance(table, str)
        assert len(table) > 0
        assert "default" in table
