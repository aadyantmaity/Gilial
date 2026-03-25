---
title: REST API
description: API endpoints and examples
---

Gilial provides REST endpoints for compression operations.

## Base URL

```
http://localhost:8000
```

(or your deployed endpoint)

## Endpoints

### GET `/status`

Get current index statistics.

**Response:**
```json
{
  "index_name": "your-index",
  "environment": "us-west-1",
  "total_vector_count": 10000,
  "dimension": 768,
  "namespaces": {}
}
```

**Example:**
```bash
curl http://localhost:8000/status
```

### GET `/estimate`

Estimate compression savings.

**Query Parameters:**
- `strategy` (optional): `"balanced"` or `"aggressive"` (default: `"balanced"`)

**Response:**
```json
{
  "original_vectors": 10000,
  "compressed_vectors": 9739,
  "original_size_mb": 29.30,
  "compressed_size_mb": 28.53,
  "savings_pct": 2.61,
  "compression_ratio": 0.974
}
```

**Example:**
```bash
curl "http://localhost:8000/estimate?strategy=balanced"
```

### POST `/compress`

Compress vectors (dry-run or apply).

**Request Body:**
```json
{
  "strategy": "balanced",
  "dry_run": true
}
```

**Parameters:**
- `strategy` (str): `"balanced"` or `"aggressive"` (default: `"balanced"`)
- `dry_run` (bool): Preview only (default: `true`)

**Response:**
```json
{
  "strategy": "balanced",
  "original_vectors": 10000,
  "compressed_vectors": 9739,
  "original_size_mb": 29.30,
  "compressed_size_mb": 28.53,
  "dry_run": false,
  "savings_pct": 2.61,
  "metadata": {
    "deleted_vectors": 261
  }
}
```

**Example - Dry-Run:**
```bash
curl -X POST http://localhost:8000/compress \
  -H "Content-Type: application/json" \
  -d '{"strategy": "balanced", "dry_run": true}'
```

**Example - Apply:**
```bash
curl -X POST http://localhost:8000/compress \
  -H "Content-Type: application/json" \
  -d '{"strategy": "balanced", "dry_run": false}'
```

## Running the Server

```bash
python backend/main.py
```

Server starts at `http://localhost:8000`

## Rate Limiting

No built-in rate limits. Recommended:
- Limit compression runs to once per hour
- Run during off-peak times
- Use dry-run before applying changes
