from unittest.mock import MagicMock, patch
from gilial.evaluator import CompressionEvaluator
from gilial.metrics import EvalReport
from gilial.canary import CanarySet, CanaryVerificationResult


class TestCompressionEvaluator:
    def test_run_returns_eval_report(self, mock_writer, sample_memories, embedding_dispatcher):
        for content, tags, emb in sample_memories:
            embedding_dispatcher.register(content, emb)
            mock_writer.store(content, tags=tags)

        evaluator = CompressionEvaluator(mock_writer)
        report = evaluator.run(dry_run=True)

        assert isinstance(report, EvalReport)
        assert isinstance(report.retrieval.ndcg, float)
        assert isinstance(report.storage.memories_before, int)
        assert isinstance(report.false_deletion.false_deletion_rate, float)
        assert isinstance(report.coverage_retention, float)
        assert isinstance(report.timestamp, str)
        assert isinstance(report.passed, bool)

    def test_baseline_returns_dict_with_query_keys(self, mock_writer, sample_memories, embedding_dispatcher):
        for content, tags, emb in sample_memories:
            embedding_dispatcher.register(content, emb)
            mock_writer.store(content, tags=tags)

        evaluator = CompressionEvaluator(mock_writer)
        queries = [{"query": "rivers"}, {"query": "python language"}]
        result = evaluator.baseline(queries, k=3)

        assert isinstance(result, dict)
        for q in queries:
            assert q["query"] in result
            assert isinstance(result[q["query"]], list)

    def test_passed_false_when_canary_lost(self, mock_writer, sample_memories, embedding_dispatcher):
        for content, tags, emb in sample_memories:
            embedding_dispatcher.register(content, emb)
            mock_writer.store(content, tags=tags)

        canary_set = CanarySet()
        canary_set._canary_ids = ["fake-canary-id-1", "fake-canary-id-2"]

        evaluator = CompressionEvaluator(mock_writer, canary_set=canary_set)
        report = evaluator.run(dry_run=True)

        assert report.false_deletion.false_deletion_rate > 0.0
        assert report.passed is False
