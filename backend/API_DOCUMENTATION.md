# Gilial API Documentation

**Version:** 0.1.0
**Base URL:** `http://localhost:8000` (development)


## Base URL & Versioning

All endpoints are under `/api/v1/` in future versions. Current version uses `/api/`.

**Health Check (No Auth Required)**
```
GET /api/health
```

---

## Error Handling

All errors follow this format:

```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "details": "Optional additional context"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (validation error) |
| 404 | Connection not found |
| 500 | Server error |
| 503 | Service unavailable (Pinecone connection failed) |

### Common Error Types

- `validation_error`: Configuration validation failed
- `connection_error`: Failed to connect to Pinecone
- `not_found`: Connection ID doesn't exist
- `server_error`: Unexpected server error

---

## Endpoints

### 1. Health Check

**Endpoint:** `GET /api/health`

**Description:** Check if the API is running.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

**Example:**
```bash
curl http://localhost:8000/api/health
```

---

### 2. Create Connection

**Endpoint:** `POST /api/connections`

**Description:** Establish a new connection to a Pinecone index. Returns a `connection_id` for use in subsequent API calls.

**Request Body:**
```json
{
  "api_key": "your-pinecone-api-key",
  "index_name": "my-index",
  "environment": "us-west-1",
  "namespace": "optional-namespace"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `api_key` | string | Yes | Your Pinecone API key |
| `index_name` | string | Yes | Name of the Pinecone index |
| `environment` | string | Yes | Pinecone environment (e.g., `us-west-1`) |
| `namespace` | string | No | Optional namespace within the index |

**Response (200):**
```json
{
  "connection_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "connected",
  "index_stats": {
    "index_name": "my-index",
    "environment": "us-west-1",
    "total_vector_count": 100000,
    "dimension": 1536,
    "namespaces": {
      "namespace1": { "vector_count": 50000 },
      "namespace2": { "vector_count": 50000 }
    }
  }
}
```

**Error (400 - Validation):**
```json
{
  "error": "validation_error",
  "message": "pinecone_api_key is required",
  "details": "One or more required fields are missing"
}
```

**Error (503 - Connection Failed):**
```json
{
  "error": "connection_error",
  "message": "Failed to connect to Pinecone index 'my-index'",
  "details": "Invalid API key or index not found"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/connections \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-api-key",
    "index_name": "my-index",
    "environment": "us-west-1"
  }'
```

---

### 3. Get Connection Status

**Endpoint:** `GET /api/connections/{connection_id}/status`

**Description:** Get current statistics about a connected Pinecone index.

**Path Parameters:**
| Field | Type | Description |
|-------|------|-------------|
| `connection_id` | string (UUID) | ID from create connection response |

**Response (200):**
```json
{
  "index_name": "my-index",
  "environment": "us-west-1",
  "total_vector_count": 100000,
  "dimension": 1536,
  "namespaces": {
    "namespace1": { "vector_count": 50000 },
    "namespace2": { "vector_count": 50000 }
  }
}
```

**Error (404):**
```json
{
  "error": "not_found",
  "message": "Connection not found",
  "details": "connection_id '550e8400-e29b-41d4-a716-446655440000' does not exist"
}
```

**Example:**
```bash
curl http://localhost:8000/api/connections/550e8400-e29b-41d4-a716-446655440000/status
```

---

### 4. Estimate Compression Savings

**Endpoint:** `GET /api/connections/{connection_id}/estimate`

**Description:** Calculate estimated compression savings without making any changes to the index.

**Path Parameters:**
| Field | Type | Description |
|-------|------|-------------|
| `connection_id` | string (UUID) | ID from create connection response |

**Query Parameters:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `strategy` | string | `balanced` | Compression strategy: `balanced`, `aggressive`, or `conservative` |

**Response (200):**
```json
{
  "strategy": "balanced",
  "original_vectors": 100000,
  "estimated_compressed_vectors": 65000,
  "estimated_deleted_vectors": 35000,
  "original_size_mb": 611.88,
  "estimated_compressed_size_mb": 398.22,
  "estimated_savings_pct": 34.9
}
```

**Compression Strategies:**

- **balanced** (default): 30-40% reduction, maintains quality
- **aggressive**: 40-50% reduction, some quality loss acceptable
- **conservative**: 20-30% reduction, minimal quality impact

**Error (404):**
```json
{
  "error": "not_found",
  "message": "Connection not found"
}
```

**Example:**
```bash
# Default balanced strategy
curl "http://localhost:8000/api/connections/550e8400-e29b-41d4-a716-446655440000/estimate"

# Aggressive compression
curl "http://localhost:8000/api/connections/550e8400-e29b-41d4-a716-446655440000/estimate?strategy=aggressive"
```

---

### 5. Compress Index

**Endpoint:** `POST /api/connections/{connection_id}/compress`

**Description:** Execute vector compression on a Pinecone index. Can run as dry-run to preview changes.

**Path Parameters:**
| Field | Type | Description |
|-------|------|-------------|
| `connection_id` | string (UUID) | ID from create connection response |

**Request Body:**
```json
{
  "strategy": "balanced",
  "dry_run": true
}
```

**Parameters:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `strategy` | string | `balanced` | Compression strategy (see above) |
| `dry_run` | boolean | `true` | If false, persists changes; if true, computes only |

**Response (200):**
```json
{
  "strategy": "balanced",
  "original_vectors": 100000,
  "compressed_vectors": 65000,
  "original_size_mb": 611.88,
  "compressed_size_mb": 398.22,
  "dry_run": true,
  "metadata": {
    "deleted_by_score": 10000,
    "merged_count": 5000,
    "summarized_count": 8000
  }
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `strategy` | string | Compression strategy used |
| `original_vectors` | int | Vectors before compression |
| `compressed_vectors` | int | Vectors after compression |
| `original_size_mb` | float | Estimated storage before (MB) |
| `compressed_size_mb` | float | Estimated storage after (MB) |
| `dry_run` | boolean | Whether changes were persisted |
| `metadata` | object | Breakdown of compression techniques |

**Error (400 - Bad Strategy):**
```json
{
  "error": "validation_error",
  "message": "Invalid compression strategy",
  "details": "strategy must be one of: balanced, aggressive, conservative"
}
```

**Error (404):**
```json
{
  "error": "not_found",
  "message": "Connection not found"
}
```

**Example:**
```bash
# Dry-run to preview changes
curl -X POST http://localhost:8000/api/connections/550e8400-e29b-41d4-a716-446655440000/compress \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "balanced",
    "dry_run": true
  }'

# Execute compression (persist changes)
curl -X POST http://localhost:8000/api/connections/550e8400-e29b-41d4-a716-446655440000/compress \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "balanced",
    "dry_run": false
  }'
```

---

## Data Models

### CreateConnectionRequest
```json
{
  "api_key": "string (required)",
  "index_name": "string (required)",
  "environment": "string (required)",
  "namespace": "string (optional)"
}
```

### CompressionResult
```json
{
  "strategy": "string",
  "original_vectors": "integer",
  "compressed_vectors": "integer",
  "original_size_mb": "float",
  "compressed_size_mb": "float",
  "dry_run": "boolean",
  "metadata": {
    "deleted_by_score": "integer",
    "merged_count": "integer",
    "summarized_count": "integer"
  }
}
```

### IndexStatus
```json
{
  "index_name": "string",
  "environment": "string",
  "total_vector_count": "integer",
  "dimension": "integer",
  "namespaces": {
    "namespace_name": {
      "vector_count": "integer"
    }
  }
}
```

---