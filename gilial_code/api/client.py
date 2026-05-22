"""Public API client for Gilial vector compression."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from gilial_code.auth.config import ConfigManager, UserConfig, validate_config
from gilial_code.api.recall import RecallReport, run_recall_benchmark, compute_recall


@dataclass
class CompressionResult:
    strategy: str
    original_vectors: int = 0
    compressed_vectors: int = 0
    original_size_mb: float = 0.0
    compressed_size_mb: float = 0.0
    dry_run: bool = True
    namespace: Optional[str] = None
    bits_per_dim: int = 4
    duration_seconds: float = 0.0
    recall: Optional["RecallReport"] = None
    metadata: dict = field(default_factory=dict)

    @property
    def compression_ratio(self) -> float:
        if self.original_size_mb == 0:
            return 0.0
        return self.compressed_size_mb / self.original_size_mb

    @property
    def savings_pct(self) -> float:
        return (1 - self.compression_ratio) * 100

    def to_dict(self) -> dict:
        d = {
            "strategy": self.strategy,
            "namespace": self.namespace,
            "bits_per_dim": self.bits_per_dim,
            "dry_run": self.dry_run,
            "original_vectors": self.original_vectors,
            "compressed_vectors": self.compressed_vectors,
            "original_size_mb": self.original_size_mb,
            "compressed_size_mb": self.compressed_size_mb,
            "compression_ratio": round(self.compression_ratio, 4),
            "savings_pct": round(self.savings_pct, 2),
            "duration_seconds": self.duration_seconds,
            "recall": self.recall.to_dict() if self.recall else None,
        }
        return d


class PineconeCompressionClient:
    """Main client for compressing vectors stored in a Pinecone index."""

    def __init__(
        self,
        api_key: str,
        index_name: str,
        environment: str = "us-west",
        namespace: Optional[str] = None,
    ):
        config = UserConfig(
            pinecone_api_key=api_key,
            index_name=index_name,
            environment=environment,
            namespace=namespace,
        )
        errors = validate_config(config)
        if errors:
            raise ValueError(f"Invalid configuration: {'; '.join(errors)}")

        self._config_manager = ConfigManager(config)
        self._connector = None
        self._compressor = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_connector(self, namespace: Optional[str] = None):
        """Return a connector, re-using the cached one unless namespace differs."""
        effective_ns = namespace if namespace is not None else self._config_manager.config.namespace
        if self._connector is None or self._connector.namespace != effective_ns:
            from gilial_code.connectors.pinecone import PineconeConnector

            cfg = self._config_manager.config
            self._connector = PineconeConnector(
                api_key=cfg.pinecone_api_key,
                index_name=cfg.index_name,
                environment=cfg.environment,
                namespace=effective_ns,
            )
        return self._connector

    def _get_compressor(self):
        if self._compressor is None:
            from gilial_code.compression.compressor import Compressor

            self._compressor = Compressor()
        return self._compressor

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compress(
        self,
        strategy: str = "balanced",
        dry_run: bool = True,
        namespace: Optional[str] = None,
        bits_per_dim: Optional[int] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
        log_path: Optional[str] = None,
        validate_recall: bool = False,
        recall_queries: Optional[list] = None,
        recall_n_queries: int = 100,
        recall_k: int = 10,
    ) -> CompressionResult:
        """Compress vectors in the connected Pinecone index.

        Args:
            strategy: 'balanced' (4-bit, ~8x), 'aggressive' (2-bit, ~16x),
                      or 'high_quality' (6-bit, ~5x).
            dry_run: If True, compute results without writing changes.
            namespace: Target a specific namespace; overrides the client default.
            bits_per_dim: Override the strategy's default bits per dimension (2–8).
            on_progress: Callback called as ``on_progress(vectors_done, vectors_total)``
                         during live compression. Only fires when dry_run=False.
            log_path: Write a JSON log of the result to this file path.
                      Defaults to no log. Pass ``"auto"`` to write to
                      ``~/.gilial/logs/<timestamp>.json``.
            validate_recall: If True (and dry_run=False), run a recall benchmark
                             before and after compression and attach the report to
                             the result. Ignored on dry runs.
            recall_queries: Pre-built list of query vectors to use for recall
                            validation. If None, vectors are sampled from the index.
            recall_n_queries: Number of queries to auto-sample when recall_queries
                              is not provided (default 100).
            recall_k: Top-k to measure recall over (default 10).

        Returns:
            CompressionResult with compression statistics.
        """
        start = time.monotonic()
        connector = self._get_connector(namespace)
        compressor = self._get_compressor()

        stats = connector.get_index_stats()
        original_count = stats.get("total_vector_count", 0)
        dimension = stats.get("dimension", 0)
        original_size_mb = (original_count * dimension * 4) / (1024 * 1024)

        # Capture baseline recall before touching the index
        baseline_results = None
        sampled_queries = recall_queries
        time_before = 0.0
        if validate_recall and not dry_run:
            print(f"Running recall benchmark — {recall_n_queries} queries @ top-{recall_k} before compression...")
            baseline_results, sampled_queries, time_before = run_recall_benchmark(
                connector,
                queries=recall_queries,
                n_queries=recall_n_queries,
                k=recall_k,
            )

        result = compressor.compress(
            connector=connector,
            strategy=strategy,
            dry_run=dry_run,
            bits_per_dim=bits_per_dim,
            on_progress=on_progress,
        )

        compressed_size_mb = result.get("compressed_size_mb", original_size_mb)
        effective_bits = result.get("bits_per_dimension", bits_per_dim or 4)

        # Measure recall after compression
        recall_report: Optional[RecallReport] = None
        if validate_recall and not dry_run and baseline_results is not None:
            print("Running recall benchmark after compression...")
            after_results, _, time_after = run_recall_benchmark(
                connector,
                queries=sampled_queries,
                k=recall_k,
            )
            recall_report = compute_recall(baseline_results, after_results, recall_k, time_before, time_after)
            print(recall_report)

        duration = round(time.monotonic() - start, 2)

        cr = CompressionResult(
            strategy=strategy,
            original_vectors=original_count,
            compressed_vectors=result.get("compressed_vector_count", original_count),
            original_size_mb=round(original_size_mb, 2),
            compressed_size_mb=round(compressed_size_mb, 2),
            dry_run=dry_run,
            namespace=connector.namespace,
            bits_per_dim=effective_bits,
            duration_seconds=duration,
            recall=recall_report,
            metadata=result.get("metadata", {}),
        )

        if log_path is not None:
            self._write_log(cr, log_path)

        return cr

    def estimate_savings(
        self,
        strategy: str = "balanced",
        namespace: Optional[str] = None,
        bits_per_dim: Optional[int] = None,
    ) -> dict:
        """Estimate compression savings without performing any changes.

        Args:
            strategy: Compression strategy to estimate for.
            namespace: Target a specific namespace; overrides the client default.
            bits_per_dim: Override bits per dimension for the estimate.

        Returns:
            Dictionary with estimated savings.
        """
        connector = self._get_connector(namespace)
        compressor = self._get_compressor()
        stats = connector.get_index_stats()

        original_count = stats.get("total_vector_count", 0)
        dimension = stats.get("dimension", 0)
        original_size_mb = (original_count * dimension * 4) / (1024 * 1024)

        estimate_result = compressor.estimate_savings(
            connector=connector,
            strategy=strategy,
            bits_per_dim=bits_per_dim,
        )

        estimated_size_mb = estimate_result.get("estimated_compressed_size_mb", 0)
        estimated_savings_pct = estimate_result.get("estimated_savings_pct", 0)

        return {
            "namespace": connector.namespace,
            "strategy": strategy,
            "bits_per_dim": estimate_result.get("bits_per_dimension", bits_per_dim or 4),
            "original_vectors": original_count,
            "original_size_mb": round(original_size_mb, 2),
            "compressed_size_mb": round(estimated_size_mb, 2),
            "compression_ratio": round(estimated_size_mb / original_size_mb, 4) if original_size_mb > 0 else 0,
            "savings_pct": round(estimated_savings_pct, 1),
        }

    def get_status(self) -> dict:
        """Get the current status of the Pinecone index."""
        connector = self._get_connector()
        stats = connector.get_index_stats()
        return {
            "index_name": self._config_manager.config.index_name,
            "environment": self._config_manager.config.environment,
            "total_vector_count": stats.get("total_vector_count", 0),
            "dimension": stats.get("dimension", 0),
            "namespaces": stats.get("namespaces", {}),
        }

    def benchmark(
        self,
        queries: Optional[list] = None,
        n_queries: int = 100,
        k: int = 10,
        namespace: Optional[str] = None,
    ) -> RecallReport:
        """Run a standalone recall benchmark without compressing.

        Useful for establishing a baseline or testing recall after a manual change.
        Queries the index twice with the same vectors and measures top-k overlap,
        which should be ~100% on an unchanged index (confirms the benchmark itself
        is working). To measure post-compression recall, use ``compress(validate_recall=True)``.

        Args:
            queries: List of query vectors. If None, vectors are sampled from the index.
            n_queries: Number of queries to auto-sample (default 100).
            k: Top-k to measure recall over (default 10).
            namespace: Namespace to query; overrides client default.

        Returns:
            RecallReport with mean/min/max recall and per-query breakdown.

        Example::

            report = client.benchmark(n_queries=200, k=10)
            print(report)
            # Recall@10 — 200 queries
            #   mean : 100.00%
            #   min  : 100.00%
            #   max  : 100.00%
        """
        connector = self._get_connector(namespace)
        baseline, sampled_queries, t_before = run_recall_benchmark(
            connector, queries=queries, n_queries=n_queries, k=k
        )
        after, _, t_after = run_recall_benchmark(
            connector, queries=sampled_queries, k=k
        )
        return compute_recall(baseline, after, k, t_before, t_after)

    def list_namespaces(self) -> list[str]:
        """Return a list of namespace names in the index.

        Returns:
            List of namespace strings. Empty string ``""`` means the default namespace.
        """
        connector = self._get_connector()
        stats = connector.get_index_stats()
        namespaces = stats.get("namespaces", {})
        return list(namespaces.keys())

    def compress_all_namespaces(
        self,
        strategy: str = "balanced",
        dry_run: bool = True,
        bits_per_dim: Optional[int] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        log_path: Optional[str] = None,
    ) -> list[CompressionResult]:
        """Compress every namespace in the index independently.

        Args:
            strategy: Compression strategy.
            dry_run: If True, compute results without writing changes.
            bits_per_dim: Override bits per dimension.
            on_progress: Callback ``on_progress(namespace, vectors_done, vectors_total)``.
            log_path: Write a combined JSON log to this path. Pass ``"auto"`` for
                      ``~/.gilial/logs/<timestamp>_all_namespaces.json``.

        Returns:
            List of CompressionResult, one per namespace.
        """
        namespaces = self.list_namespaces()
        if not namespaces:
            namespaces = [""]

        results = []
        for ns in namespaces:
            def _cb(done: int, total: int, _ns: str = ns) -> None:
                if on_progress:
                    on_progress(_ns, done, total)

            result = self.compress(
                strategy=strategy,
                dry_run=dry_run,
                namespace=ns,
                bits_per_dim=bits_per_dim,
                on_progress=_cb,
            )
            results.append(result)

        if log_path is not None:
            self._write_combined_log(results, log_path)

        return results

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_log_path(path: str, suffix: str = "") -> str:
        if path == "auto":
            log_dir = os.path.expanduser("~/.gilial/logs")
            os.makedirs(log_dir, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            return os.path.join(log_dir, f"{ts}{suffix}.json")
        return path

    def _write_log(self, result: CompressionResult, path: str) -> None:
        resolved = self._resolve_log_path(path)
        payload = {
            "gilial_log_version": "1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "index_name": self._config_manager.config.index_name,
            "result": result.to_dict(),
        }
        with open(resolved, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"Compression log written to {resolved}")

    def _write_combined_log(self, results: list[CompressionResult], path: str) -> None:
        resolved = self._resolve_log_path(path, suffix="_all_namespaces")
        payload = {
            "gilial_log_version": "1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "index_name": self._config_manager.config.index_name,
            "namespaces_compressed": len(results),
            "results": [r.to_dict() for r in results],
        }
        with open(resolved, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"Combined compression log written to {resolved}")
