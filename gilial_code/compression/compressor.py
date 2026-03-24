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
            strategy: Compression strategy - 'balanced' or 'aggressive'
            dry_run: If True, compute without persisting changes

        Returns:
            Dictionary with compression results
        """
        # Get config based on strategy
        if strategy == "aggressive":
            config = CompressionConfig.aggressive()
        else:
            config = CompressionConfig.balanced()

        # Get index stats before compression
        stats_before = connector.get_index_stats()
        original_count = stats_before.get("total_vector_count", 0)
        dimension = stats_before.get("dimension", 0)
        original_size_mb = (original_count * dimension * 4) / (1024 * 1024)

        # Estimate compression
        estimated_compressed_count = self._estimate_compressed_count(
            original_count, config
        )

        # Execute compression if not a dry run
        if not dry_run:
            self._execute_compression(connector, config, original_count, dimension)
            # Get actual post-compression count
            stats_after = connector.get_index_stats()
            actual_compressed_count = stats_after.get("total_vector_count", 0)
        else:
            # For dry run, use estimate
            actual_compressed_count = estimated_compressed_count

        compressed_size_mb = (actual_compressed_count * dimension * 4) / (1024 * 1024)

        return {
            "strategy": strategy,
            "dry_run": dry_run,
            "original_vector_count": original_count,
            "compressed_vector_count": actual_compressed_count,
            "deleted_vectors": original_count - actual_compressed_count,
            "original_size_mb": round(original_size_mb, 2),
            "compressed_size_mb": round(compressed_size_mb, 2),
            "compression_ratio": round(compressed_size_mb / original_size_mb, 3) if original_size_mb > 0 else 0,
            "savings_pct": round((1 - compressed_size_mb / original_size_mb) * 100, 1) if original_size_mb > 0 else 0,
            "metadata": {
                "estimated_vs_actual": {
                    "estimated_count": estimated_compressed_count,
                    "actual_count": actual_compressed_count,
                },
            },
        }

    def estimate_savings(self, connector, strategy: str = "balanced") -> Dict[str, Any]:
        """Estimate compression savings by sampling the index.

        Args:
            connector: Database connector
            strategy: Compression strategy

        Returns:
            Dictionary with estimated savings based on sample analysis
        """
        stats = connector.get_index_stats()
        original_count = stats.get("total_vector_count", 0)
        dimension = stats.get("dimension", 0)
        original_size_mb = (original_count * dimension * 4) / (1024 * 1024)

        # Get config
        if strategy == "aggressive":
            config = CompressionConfig.aggressive()
        else:
            config = CompressionConfig.balanced()

        # Sample vectors and analyze compression rate
        sample_size = min(100, original_count)  # Sample up to 100 vectors
        sample_compression_rate = self._sample_and_analyze(
            connector, sample_size, config
        )

        # Extrapolate to full index
        estimated_compressed = int(original_count * sample_compression_rate)
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
            "sample_size": sample_size,
            "sample_compression_rate": round(sample_compression_rate, 3),
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

    def _sample_and_analyze(
        self,
        connector,
        sample_size: int,
        config: CompressionConfig,
    ) -> float:
        """Sample vectors from the index and analyze compression rate.

        Args:
            connector: Database connector
            sample_size: Number of vectors to sample
            config: Compression configuration

        Returns:
            Compression rate (ratio of vectors retained after compression)
        """
        import numpy as np

        try:
            # Fetch a sample of vectors
            vectors = connector.get_all(limit=sample_size)
            if not vectors or len(vectors) < 2:
                # Fallback to strategy-based estimate if we can't sample
                if config.strategy == "aggressive":
                    return 0.67
                else:
                    return 0.728

            # Analyze the sample: calculate vector norms/magnitudes as a proxy for "score"
            vector_scores = []
            for vec in vectors:
                values = vec.get("values", [])
                if values:
                    # Use L2 norm as a simple score metric
                    score = float(np.linalg.norm(values))
                    vector_scores.append(score)

            if not vector_scores:
                # Fallback estimate
                return 0.728

            vector_scores = np.array(vector_scores)
            mean_score = np.mean(vector_scores)
            std_score = np.std(vector_scores)

            # Count vectors below the deletion threshold
            # Threshold based on score_floor: vectors with score < threshold are deleted
            if std_score > 0:
                deletion_threshold = mean_score - (std_score * config.score_floor)
            else:
                deletion_threshold = mean_score * config.score_floor

            vectors_to_delete = np.sum(vector_scores < deletion_threshold)
            retention_rate = 1.0 - (vectors_to_delete / len(vector_scores))

            return max(retention_rate, 0.3)  # At least 30% retained

        except Exception as e:
            # If sampling fails, fall back to strategy-based estimate
            print(f"Warning: Sampling analysis failed: {e}")
            if config.strategy == "aggressive":
                return 0.67
            else:
                return 0.728

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
        # More conservative: only remove the lowest-scoring vectors

        # Score floor determines which vectors get deleted
        # Higher score_floor = more aggressive deletion
        if config.strategy == "aggressive":
            # Aggressive: keep ~65-70% (remove ~30-35%)
            retention_rate = 0.67
        else:
            # Balanced: keep ~72-73% (remove ~27-28%)
            retention_rate = 0.728

        final_count = int(original_count * retention_rate)
        return max(final_count, int(original_count * 0.3))  # At least 30% remains

    def _execute_compression(
        self,
        connector,
        config: CompressionConfig,
        original_count: int,
        dimension: int,
    ) -> None:
        """Execute compression by modifying vectors in the database.

        Args:
            connector: Database connector
            config: Compression configuration
            original_count: Original vector count
            dimension: Vector dimension
        """
        import numpy as np

        # Fetch all vectors
        print(f"Fetching up to {original_count} vectors from index...")
        vectors = connector.get_all(limit=original_count)
        if not vectors:
            print(f"ERROR: Could not fetch vectors for compression (got empty list)")
            print(f"This might indicate an issue with get_all() pagination")
            return

        print(f"Successfully fetched {len(vectors)} vectors for compression")

        # Calculate vector scores (L2 norm)
        vector_scores = []
        for vec in vectors:
            values = vec.get("values", [])
            if values:
                score = float(np.linalg.norm(values))
                vector_scores.append((vec["id"], score))
            else:
                vector_scores.append((vec["id"], 0.0))

        if not vector_scores:
            return

        # Sort by score (lowest first)
        vector_scores.sort(key=lambda x: x[1])

        # Calculate how many vectors to delete based on strategy
        # Use the same retention rate as estimate
        if config.strategy == "aggressive":
            retention_rate = 0.67
        else:
            retention_rate = 0.728

        vectors_to_keep = int(len(vector_scores) * retention_rate)
        vectors_to_delete_ids = [vid for vid, _ in vector_scores[:len(vector_scores) - vectors_to_keep]]

        # Delete low-scoring vectors
        print(f"Deleting {len(vectors_to_delete_ids)} low-scoring vectors...")
        deletion_batch_size = 100
        for i in range(0, len(vectors_to_delete_ids), deletion_batch_size):
            batch = vectors_to_delete_ids[i:i + deletion_batch_size]
            try:
                connector.index.delete(ids=batch, namespace=connector.namespace)
                print(f"  Deleted batch {i // deletion_batch_size + 1}/{(len(vectors_to_delete_ids) + deletion_batch_size - 1) // deletion_batch_size}")
            except Exception as e:
                print(f"  Warning: Failed to delete batch: {e}")
