---
title: Quick Start
description: Get up and running in 5 minutes
---

Get up and running with Gilial's REST API in 5 minutes.

## 1. Set Up Your Credentials

Configure your Pinecone credentials in your terminal:

```bash
export PINECONE_API_KEY="your-pinecone-api-key"
export PINECONE_INDEX_NAME="your-index-name"
export PINECONE_ENVIRONMENT="us-west-1"  # or your region
```

## 2. Start the Gilial Server

Start the Gilial backend:

```bash
python backend/main.py
```

Server will start at `http://localhost:8000`

## 3. Check Your Index

```bash
curl http://localhost:8000/status
```

Response:
```json
{
  "index_name": "your-index",
  "total_vector_count": 10000,
  "dimension": 768
}
```

## 4. Estimate Savings

Preview how much space you'll save:

```bash
curl http://localhost:8000/estimate?strategy=balanced
```

Response:
```json
{
  "original_vectors": 10000,
  "compressed_vectors": 9739,
  "savings_pct": 2.61
}
```

## 5. Run Compression

### Dry-Run Mode (Preview Only)

```bash
curl -X POST http://localhost:8000/compress \
  -H "Content-Type: application/json" \
  -d '{"strategy": "balanced", "dry_run": true}'
```

### Apply Compression

```bash
curl -X POST http://localhost:8000/compress \
  -H "Content-Type: application/json" \
  -d '{"strategy": "balanced", "dry_run": false}'
```

## Choose Your Strategy

- **Balanced** (default) - Good mix of compression and safety
- **Aggressive** - Maximum compression for space-critical scenarios

## Next Steps

- Learn about [Compression Strategies](../guides/strategies.md)
- Read [Best Practices](../guides/best-practices.md)
- Check the [REST API Reference](../api/rest-api.md)
