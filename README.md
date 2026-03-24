# Gilial

Gilial is a vector compression system for Pinecone indexes. It intelligently removes low-scoring vectors to reduce storage costs while maintaining search quality.

## Quick Start

1. **Setup**: Configure your Pinecone API key and index name in your terminal
2. **Run Compression**: Execute the compression algorithm with your preferred strategy (Balanced or Aggressive)
3. **Monitor**: Track compression impact through generated metrics and visualizations

## Key Documents

- **[analysis.md](analysis.md)** - Compression test results, impact metrics, and visualizations
- **[backend/API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md)** - API endpoints and client usage
- **[gilial_code/compression/](gilial_code/compression/)** - Compression algorithm implementations

## Features

- **Selective Compression**: Remove only low-scoring vectors based on L2 norm
- **Multiple Strategies**: Choose between Balanced or Aggressive approaches
- **Dry-Run Mode**: Preview compression impact before applying changes
- **Performance Metrics**: Detailed analysis of vector reduction and storage savings

## Architecture

```
gilial_code/
├── api/          # HTTP API client for compression
├── compression/  # Compression algorithms and strategies
└── connectors/   # Pinecone integration

backend/         # API server and main entry point
testing/         # Test scripts and compression analysis
```

## Getting Started

See [analysis.md](analysis.md) for test setup and results, or [backend/API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md) for API usage details.
