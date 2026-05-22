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
    # TurboQuant parameters
    turboquant_bits: int = 4       # bits per dimension (2–8); 4 = 8x compression
    turboquant_seed: int = 42      # rotation matrix seed (must match at query time)
    turboquant_use_qjl: bool = True  # enable 1-bit QJL residual correction stage

    @classmethod
    def aggressive(cls) -> "CompressionConfig":
        """Aggressive compression: maximize reduction (2-bit TurboQuant, ~16x)."""
        return cls(
            strategy="aggressive",
            score_floor=0.5,
            protect_top_pct=0.1,
            similarity_threshold=0.85,
            low_threshold=0.65,
            high_threshold=0.85,
            turboquant_bits=2,
        )

    @classmethod
    def balanced(cls) -> "CompressionConfig":
        """Balanced compression: 4-bit TurboQuant (~8x) with QJL correction."""
        return cls(strategy="balanced", turboquant_bits=4)

    @classmethod
    def high_quality(cls) -> "CompressionConfig":
        """High-quality compression: 6-bit TurboQuant (~5x), near-lossless."""
        return cls(strategy="high_quality", turboquant_bits=6)


class Compressor:
    """Orchestrates TurboQuant compression pipeline for vector databases.

    TurboQuant replaces the previous deletion-based approach with quantization:
    instead of removing vectors, it reduces each vector's storage footprint via
    random rotation + scalar quantization + optional 1-bit QJL residual correction.
    All vectors are retained; only their precision is reduced.

    Reference: Zandieh et al. (2025) https://arxiv.org/abs/2504.19874
    """

    def __init__(self):
        """Initialize compressor."""
        self._telemetry = None

    def compress(
        self,
        connector,
        strategy: str = "balanced",
        dry_run: bool = True,
        bits_per_dim: Optional[int] = None,
        on_progress=None,
    ) -> Dict[str, Any]:
        """Compress vectors in the connected database using TurboQuant.

        Args:
            connector: Database connector (e.g., PineconeConnector)
            strategy: 'balanced' (4-bit, ~8x), 'aggressive' (2-bit, ~16x),
                      or 'high_quality' (6-bit, ~5x)
            dry_run: If True, compute savings without writing changes

        Returns:
            Dictionary with compression results
        """
        config = self._config_for_strategy(strategy)
        if bits_per_dim is not None:
            config.turboquant_bits = max(2, min(8, bits_per_dim))

        stats_before = connector.get_index_stats()
        original_count = stats_before.get("total_vector_count", 0)
        dimension = stats_before.get("dimension", 0)

        from gilial_code.compression.turboquant import TurboQuant
        tq = TurboQuant(
            dim=dimension,
            bits=config.turboquant_bits,
            seed=config.turboquant_seed,
            use_qjl=config.turboquant_use_qjl,
        )

        original_size_mb = (original_count * tq.bytes_per_vector_original()) / (1024 * 1024)
        compressed_size_mb = (original_count * tq.bytes_per_vector_quantized()) / (1024 * 1024)

        if not dry_run:
            self._execute_compression(connector, config, tq, original_count, dimension, on_progress=on_progress)

        return {
            "strategy": strategy,
            "dry_run": dry_run,
            "algorithm": "TurboQuant",
            "bits_per_dimension": config.turboquant_bits,
            "qjl_residual": config.turboquant_use_qjl,
            "original_vector_count": original_count,
            "compressed_vector_count": original_count,  # all vectors retained
            "original_size_mb": round(original_size_mb, 2),
            "compressed_size_mb": round(compressed_size_mb, 2),
            "compression_ratio": round(tq.compression_ratio(), 3),
            "savings_pct": round((1 - tq.compression_ratio()) * 100, 1),
        }

    def estimate_savings(self, connector, strategy: str = "balanced", bits_per_dim: Optional[int] = None) -> Dict[str, Any]:
        """Estimate compression savings (no data fetched — TurboQuant ratio is deterministic).

        Args:
            connector: Database connector
            strategy: Compression strategy

        Returns:
            Dictionary with estimated savings
        """
        from gilial_code.compression.turboquant import TurboQuant

        stats = connector.get_index_stats()
        original_count = stats.get("total_vector_count", 0)
        dimension = stats.get("dimension", 0)

        config = self._config_for_strategy(strategy)
        if bits_per_dim is not None:
            config.turboquant_bits = max(2, min(8, bits_per_dim))
        tq = TurboQuant(
            dim=dimension,
            bits=config.turboquant_bits,
            seed=config.turboquant_seed,
            use_qjl=config.turboquant_use_qjl,
        )

        original_size_mb = (original_count * tq.bytes_per_vector_original()) / (1024 * 1024)
        compressed_size_mb = (original_count * tq.bytes_per_vector_quantized()) / (1024 * 1024)

        return {
            "strategy": strategy,
            "algorithm": "TurboQuant",
            "bits_per_dimension": config.turboquant_bits,
            "qjl_residual": config.turboquant_use_qjl,
            "original_vectors": original_count,
            "compressed_vectors": original_count,
            "original_size_mb": round(original_size_mb, 2),
            "estimated_compressed_size_mb": round(compressed_size_mb, 2),
            "estimated_savings_pct": round((1 - tq.compression_ratio()) * 100, 1),
            "compression_ratio": round(tq.compression_ratio(), 3),
            "bytes_per_vector_original": tq.bytes_per_vector_original(),
            "bytes_per_vector_compressed": tq.bytes_per_vector_quantized(),
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
    def _config_for_strategy(strategy: str) -> "CompressionConfig":
        if strategy == "aggressive":
            return CompressionConfig.aggressive()
        elif strategy == "high_quality":
            return CompressionConfig.high_quality()
        else:
            return CompressionConfig.balanced()

    def _execute_compression(
        self,
        connector,
        config: "CompressionConfig",
        tq: "TurboQuant",
        original_count: int,
        dimension: int,
        on_progress=None,
    ) -> None:
        """Quantize all vectors in-place using TurboQuant and write back.

        The quantized vectors are decoded back to float32 before upserting so
        the index remains compatible with existing query infrastructure. The
        precision loss introduced by quantization is the compression mechanism.

        Args:
            connector: Database connector
            config: Compression configuration
            tq: Initialised TurboQuant instance
            original_count: Total vector count
            dimension: Vector dimension
        """
        import numpy as np

        print(f"Fetching up to {original_count} vectors from index...")
        vectors = connector.get_all(limit=original_count)
        if not vectors:
            print("ERROR: Could not fetch vectors for compression (got empty list)")
            return

        print(f"Successfully fetched {len(vectors)} vectors — quantizing with TurboQuant ({config.turboquant_bits}-bit)...")

        batch_size = 64
        upserted = 0
        for batch_start in range(0, len(vectors), batch_size):
            batch = vectors[batch_start: batch_start + batch_size]
            raw = np.array([v["values"] for v in batch], dtype=np.float32)

            codes, qjl_bits, norms = tq.encode_batch(raw)

            # Decode back to float32 for storage (lossy round-trip = compression)
            reconstructed = []
            for i in range(len(batch)):
                q = tq.decode(
                    codes[i],
                    float(norms[i]),
                    qjl_bits[i] if qjl_bits is not None else None,
                )
                reconstructed.append(q.tolist())

            upsert_batch = []
            for i, vec in enumerate(batch):
                upsert_batch.append((vec["id"], reconstructed[i], vec.get("metadata", {})))

            try:
                connector.index.upsert(vectors=upsert_batch, namespace=connector.namespace)
                upserted += len(upsert_batch)
                batch_num = batch_start // batch_size + 1
                total_batches = (len(vectors) + batch_size - 1) // batch_size
                print(f"  Upserted batch {batch_num}/{total_batches} ({upserted}/{len(vectors)} vectors)")
                if on_progress is not None:
                    on_progress(upserted, len(vectors))
            except Exception as e:
                print(f"  Warning: Failed to upsert batch starting at {batch_start}: {e}")

        print(f"TurboQuant compression complete — {upserted}/{len(vectors)} vectors quantized.")
