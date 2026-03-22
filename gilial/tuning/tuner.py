from __future__ import annotations

from dataclasses import dataclass, field

from gilial.eval.metrics import EvalReport
from gilial.eval.evaluator import CompressionEvaluator


@dataclass
class TuneConfig:
    score_floor: float = 0.2
    protect_top_pct: float = 0.2
    similarity_threshold: float = 0.92
    low_threshold: float = 0.75
    high_threshold: float = 0.92


@dataclass
class TuneResult:
    config: TuneConfig
    report: EvalReport
    label: str


class CompressionTuner:
    def __init__(self):
        self._configs: list[tuple[str, TuneConfig]] = []

    def add_config(self, label: str, config: TuneConfig):
        self._configs.append((label, config))

    def run_all(self, writer, dry_run=True) -> list[TuneResult]:
        results = []
        for label, config in self._configs:
            evaluator = CompressionEvaluator(writer)
            writer_kwargs_delete = dict(
                score_floor=config.score_floor,
                protect_top_pct=config.protect_top_pct,
            )
            writer_kwargs_merge = dict(
                similarity_threshold=config.similarity_threshold,
            )
            writer_kwargs_summarize = dict(
                low_threshold=config.low_threshold,
                high_threshold=config.high_threshold,
            )

            # Temporarily override compress methods to use tuned params
            orig_delete = writer.compress_delete
            orig_merge = writer.compress_merge
            orig_summarize = writer.compress_summarize

            def _patched_delete(dry_run=dry_run, _kw=writer_kwargs_delete, _orig=orig_delete):
                return _orig(dry_run=dry_run, **_kw)

            def _patched_merge(dry_run=dry_run, _kw=writer_kwargs_merge, _orig=orig_merge):
                return _orig(dry_run=dry_run, **_kw)

            def _patched_summarize(dry_run=dry_run, _kw=writer_kwargs_summarize, _orig=orig_summarize):
                return _orig(dry_run=dry_run, **_kw)

            writer.compress_delete = _patched_delete
            writer.compress_merge = _patched_merge
            writer.compress_summarize = _patched_summarize

            try:
                report = evaluator.run(dry_run=dry_run)
            finally:
                writer.compress_delete = orig_delete
                writer.compress_merge = orig_merge
                writer.compress_summarize = orig_summarize

            results.append(TuneResult(config=config, report=report, label=label))
        return results

    def best(self, results: list[TuneResult], prefer: str = "balanced") -> TuneResult:
        if prefer == "balanced":
            return max(
                results,
                key=lambda r: r.report.retrieval.ndcg * (1 - r.report.false_deletion.false_deletion_rate),
            )
        elif prefer == "aggressive":
            return max(results, key=lambda r: r.report.storage.reduction_ratio)
        elif prefer == "safe":
            return min(
                results,
                key=lambda r: (r.report.false_deletion.false_deletion_rate, -r.report.retrieval.ndcg),
            )
        else:
            raise ValueError(f"Unknown prefer mode: {prefer}")

    def summary_table(self, results: list[TuneResult]) -> str:
        header = f"{'Label':<20} {'NDCG':>6} {'MRR':>6} {'Reduction':>10} {'FD Rate':>8} {'Coverage':>9} {'Pass':>5}"
        sep = "-" * len(header)
        lines = [header, sep]
        for r in results:
            lines.append(
                f"{r.label:<20} "
                f"{r.report.retrieval.ndcg:>6.3f} "
                f"{r.report.retrieval.mrr:>6.3f} "
                f"{r.report.storage.reduction_ratio:>10.3f} "
                f"{r.report.false_deletion.false_deletion_rate:>8.3f} "
                f"{r.report.coverage_retention:>9.3f} "
                f"{'Y' if r.report.passed else 'N':>5}"
            )
        return "\n".join(lines)
