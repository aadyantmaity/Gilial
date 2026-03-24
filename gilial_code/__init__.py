"""Gilial vector compression product for Pinecone databases."""

__version__ = "0.1.0"

from gilial_code.api.client import PineconeCompressionClient, CompressionResult
from gilial_code.auth.config import ConfigManager, UserConfig
from gilial_code.compression.compressor import Compressor, CompressionConfig
from gilial_code.connectors.pinecone import PineconeConnector

__all__ = [
    "PineconeCompressionClient",
    "CompressionResult",
    "ConfigManager",
    "UserConfig",
    "Compressor",
    "CompressionConfig",
    "PineconeConnector",
]
