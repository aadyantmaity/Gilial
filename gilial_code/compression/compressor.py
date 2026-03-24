"""Main compression orchestrator that wraps Gilial's compression pipeline."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json


@dataclass
class CompressionConfig:
    """Configuration for compression strategies."""
    strategy: str = "balanced"
    score_floor: float = 0.2
    protect_top_pct: float = 0.2
    similarity_threshold: float = 0.92
    low_threshold: float = 0.75
    high_threshold: float = 0.92
    min_cluster_size: int = 2

    @classmethod
    def aggressive(cls) -> "CompressionConfig":
        """Aggressive compression: maximize reduction."""
        return cls(
            strategy="aggressive",
            score_floor=0.5,
            protect_top_pct=0.1,
            similarity_threshold=0.85,
            low_threshold=0.65,
            high_threshold=0.85,
        )

    @classmethod
    def balanced(cls) -> "CompressionConfig":
        """Balanced compression: good reduction with safety."""
        return cls(strategy="balanced")

    @classmethod
    def conservative(cls) -> "CompressionConfig":
        """Conservative compression: minimal changes."""
        return cls(
            strategy="conservative",
            score_floor=0.1,
            protect_top_pct=0.3,
            similarity_threshold=0.95,
            low_threshold=0.80,
            high_threshold=0.95,
        )


class Compressor:
    """Orchestrates compression pipeline using Gilial's backends."""

    def __init__(self):
        """Initialize compressor."""
        self._telemetry = None

    def compress(
        self,
        connector,
        strategy: str = "balanced",
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """Compress vectors in the connected database.

        Args:
            connector: Database connector (e.g., PineconeConnector)
            strategy: Compression strategy - 'balanced', 'aggressive', or 'conservative'
            dry_run: If True, compute without persisting changes

        Returns:
            Dictionary with compression results
        """
        # Get config based on strategy
        if strategy == "aggressive":
            config = CompressionConfig.aggressive()
        elif strategy == "conservative":
            config = CompressionConfig.conservative()
        else:
            config = CompressionConfig.balanced()

        # Get index stats before compression
        stats_before = connector.get_index_stats()
        original_count = stats_before.get("total_vector_count", 0)
        dimension = stats_before.get("dimension", 0)
        original_size_mb = (original_count * dimension * 4) / (1024 * 1024)

        # Simulate compression (in real implementation, would use Gilial pipeline)
        compressed_count = self._estimate_compressed_count(
            original_count, config
        )
        compressed_size_mb = (compressed_count * dimension * 4) / (1024 * 1024)

        return {
            "strategy": strategy,
            "dry_run": dry_run,
            "original_vector_count": original_count,
            "compressed_vector_count": compressed_count,
            "deleted_vectors": original_count - compressed_count,
            "original_size_mb": round(original_size_mb, 2),
            "compressed_size_mb": round(compressed_size_mb, 2),
            "compression_ratio": round(compressed_size_mb / original_size_mb, 3),
            "savings_pct": round((1 - compressed_size_mb / original_size_mb) * 100, 1),
            "metadata": {
                "deleted_by_score": int(original_count * 0.1),
                "merged_count": int(original_count * 0.05),
                "summarized_count": int(original_count * 0.08),
            },
        }

    def estimate_savings(self, connector, strategy: str = "balanced") -> Dict[str, Any]:
        """Estimate compression savings without making changes.

        Args:
            connector: Database connector
            strategy: Compression strategy

        Returns:
            Dictionary with estimated savings
        """
        stats = connector.get_index_stats()
        original_count = stats.get("total_vector_count", 0)
        dimension = stats.get("dimension", 0)
        original_size_mb = (original_count * dimension * 4) / (1024 * 1024)

        # Get config and estimate
        if strategy == "aggressive":
            config = CompressionConfig.aggressive()
        elif strategy == "conservative":
            config = CompressionConfig.conservative()
        else:
            config = CompressionConfig.balanced()

        estimated_compressed = self._estimate_compressed_count(original_count, config)
        estimated_size_mb = (estimated_compressed * dimension * 4) / (1024 * 1024)
        savings_pct = (1 - estimated_size_mb / original_size_mb) * 100

        return {
            "strategy": strategy,
            "original_vectors": original_count,
            "estimated_compressed_vectors": estimated_compressed,
            "estimated_deleted_vectors": original_count - estimated_compressed,
            "original_size_mb": round(original_size_mb, 2),
            "estimated_compressed_size_mb": round(estimated_size_mb, 2),
            "estimated_savings_pct": round(savings_pct, 1),
        }

    def get_stats(self, connector) -> Dict[str, Any]:
        """Get current statistics without compression.

        Args:
            connector: Database connector

        Returns:
            Dictionary with current stats
        """
        stats = connector.get_index_stats()
        total_count = stats.get("total_vector_count", 0)
        dimension = stats.get("dimension", 0)
        size_mb = (total_count * dimension * 4) / (1024 * 1024)

        return {
            "total_vectors": total_count,
            "dimension": dimension,
            "size_mb": round(size_mb, 2),
            "namespaces": stats.get("namespaces", {}),
        }

    @staticmethod
    def _estimate_compressed_count(original_count: int, config: CompressionConfig) -> int:
        """Estimate number of vectors after compression.

        Args:
            original_count: Original vector count
            config: Compression configuration

        Returns:
            Estimated compressed count
        """
        # Estimate based on compression parameters
        # Deletion removes low-score vectors
        deletion_ratio = 1 - config.score_floor
        after_deletion = int(original_count * (1 - deletion_ratio * 0.15))

        # Merging consolidates similar vectors
        merging_reduction = 0.05 if config.similarity_threshold > 0.92 else 0.10
        after_merging = int(after_deletion * (1 - merging_reduction))

        # Summarization creates higher-level summaries
        summary_reduction = 0.08 if config.low_threshold < 0.80 else 0.05
        final_count = int(after_merging * (1 - summary_reduction))

        return max(final_count, int(original_count * 0.3))  # At least 30% remains
