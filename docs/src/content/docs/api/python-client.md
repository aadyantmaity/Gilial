---
title: Python Client API
description: Complete Python client reference
---

# Python Client API

The Gilial Python client provides a simple interface for vector compression.

## Installation

```bash
pip install gilial
```

## Basic Usage

```python
from gilial_code.api.client import PineconeCompressionClient

# Initialize client
client = PineconeCompressionClient(
    api_key="your-pinecone-api-key",
    index_name="your-index-name",
    environment="us-west-1"
)
```

## Methods

### `get_status()`

Get current index statistics.

**Returns:**
```python
{
    'index_name': 'your-index',
    'environment': 'us-west-1',
    'total_vector_count': 10000,
    'dimension': 768,
    'namespaces': {...}
}
```

**Example:**
```python
status = client.get_status()
print(f"Index size: {status['total_vector_count']} vectors")
```

### `estimate_savings()`

Estimate compression savings by sampling vectors.

**Returns:**
```python
{
    'original_vectors': 10000,
    'compressed_vectors': 9739,
    'original_size_mb': 29.30,
    'compressed_size_mb': 28.53,
    'savings_pct': 2.61,
    'compression_ratio': 0.974
}
```

**Example:**
```python
savings = client.estimate_savings()
if savings['savings_pct'] > 2.0:
    print(f"Good savings potential: {savings['savings_pct']}%")
```

### `compress(strategy="balanced", dry_run=True)`

Compress vectors in the index.

**Parameters:**
- `strategy` (str): `"balanced"` or `"aggressive"` (default: `"balanced"`)
- `dry_run` (bool): Preview only if True (default: `True`)

**Returns:**
```python
CompressionResult(
    strategy='balanced',
    original_vectors=10000,
    compressed_vectors=9739,
    original_size_mb=29.30,
    compressed_size_mb=28.53,
    dry_run=False,
    metadata={...}
)
```

**Example - Dry-Run:**
```python
preview = client.compress(strategy="balanced", dry_run=True)
print(f"Would save {preview.savings_pct}%")
```

**Example - Apply:**
```python
result = client.compress(strategy="balanced", dry_run=False)
print(f"Compressed! New size: {result.compressed_size_mb} MB")
```

## Strategies

### Balanced (Default)
- Retention: 72.8%
- Use for: Production, safety-first
- Deletion: ~27.2% of vectors

### Aggressive
- Retention: 67%
- Use for: Cost optimization
- Deletion: ~33% of vectors

## Error Handling

```python
try:
    result = client.compress(dry_run=False)
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Compression failed: {e}")
```

## Complete Example

```python
from gilial_code.api.client import PineconeCompressionClient

# Initialize
client = PineconeCompressionClient(
    api_key="pk-xxxxx",
    index_name="my-index",
    environment="us-west-1"
)

# Check status
status = client.get_status()
print(f"Current size: {status['total_vector_count']} vectors")

# Estimate savings
savings = client.estimate_savings()
print(f"Potential savings: {savings['savings_pct']}%")

# Preview compression
preview = client.compress(strategy="balanced", dry_run=True)
print(f"Preview - would delete {preview.metadata['deleted_vectors']} vectors")

# Apply if happy
if preview.savings_pct > 2.0:
    result = client.compress(strategy="balanced", dry_run=False)
    print(f"Done! Compressed to {result.compressed_size_mb} MB")
```
