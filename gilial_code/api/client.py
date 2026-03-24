"""Public API client for Gilial vector compression."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from gilial_code.auth.config import ConfigManager, UserConfig, validate_config


@dataclass
class CompressionResult:
    strategy: str
    original_vectors: int = 0
    compressed_vectors: int = 0
    original_size_mb: float = 0.0
    compressed_size_mb: float = 0.0
    dry_run: bool = True
    metadata: dict = field(default_factory=dict)

    @property
    def compression_ratio(self) -> float:
        if self.original_size_mb == 0:
            return 0.0
        return self.compressed_size_mb / self.original_size_mb

    @property
    def savings_pct(self) -> float:
        return (1 - self.compression_ratio) * 100


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

    def _get_connector(self):
        if self._connector is None:
            from gilial_code.connectors.pinecone import PineconeConnector

            cfg = self._config_manager.config
            self._connector = PineconeConnector(
                api_key=cfg.pinecone_api_key,
                index_name=cfg.index_name,
                environment=cfg.environment,
                namespace=cfg.namespace,
            )
        return self._connector

    def _get_compressor(self):
        if self._compressor is None:
            from gilial_code.compression.compressor import Compressor

            self._compressor = Compressor()
        return self._compressor

    def compress(
        self, strategy: str = "balanced", dry_run: bool = True
    ) -> CompressionResult:
        """Compress vectors in the connected Pinecone index.

        Args:
            strategy: Compression strategy - 'balanced', 'aggressive', or 'conservative'.
            dry_run: If True, compute results without writing changes.

        Returns:
            CompressionResult with compression statistics.
        """
        connector = self._get_connector()
        compressor = self._get_compressor()

        stats = connector.get_index_stats()
        original_count = stats.get("total_vector_count", 0)
        dimension = stats.get("dimension", 0)
        original_size_mb = (original_count * dimension * 4) / (1024 * 1024)

        result = compressor.compress(
            connector=connector,
            strategy=strategy,
            dry_run=dry_run,
        )

        compressed_count = result.get("compressed_vector_count", original_count)
        compressed_size_mb = result.get("compressed_size_mb", original_size_mb)

        return CompressionResult(
            strategy=strategy,
            original_vectors=original_count,
            compressed_vectors=compressed_count,
            original_size_mb=original_size_mb,
            compressed_size_mb=compressed_size_mb,
            dry_run=dry_run,
            metadata=result.get("metadata", {}),
        )

    def estimate_savings(self) -> dict:
        """Estimate compression savings without performing any changes."""
        connector = self._get_connector()
        stats = connector.get_index_stats()

        original_count = stats.get("total_vector_count", 0)
        dimension = stats.get("dimension", 0)
        original_size_mb = (original_count * dimension * 4) / (1024 * 1024)

        estimated_ratio = 0.45  # balanced default estimate
        return {
            "original_vectors": original_count,
            "dimension": dimension,
            "original_size_mb": round(original_size_mb, 2),
            "estimated_compressed_size_mb": round(original_size_mb * estimated_ratio, 2),
            "estimated_savings_pct": round((1 - estimated_ratio) * 100, 1),
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

    def rollback(self):
        """Rollback the last compression operation. (Not yet implemented.)"""
        raise NotImplementedError("Rollback support is planned for a future release.")
