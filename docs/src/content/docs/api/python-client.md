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

## Initialisation

```python
from gilial_code.api.client import PineconeCompressionClient

client = PineconeCompressionClient(
    api_key="your-pinecone-api-key",
    index_name="your-index-name",
    environment="us-west-1",
    namespace="my-namespace",   # optional — default namespace
)
```

---

## Methods

### `get_status()`

Get current index statistics.

```python
status = client.get_status()
# {
#   'index_name': 'your-index',
#   'environment': 'us-west-1',
#   'total_vector_count': 10000,
#   'dimension': 1536,
#   'namespaces': {'docs': {...}, 'prod': {...}}
# }
```

---

### `estimate_savings(strategy, namespace, bits_per_dim)`

Estimate compression savings without touching the index. The ratio is deterministic for TurboQuant so no vectors need to be fetched.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy` | str | `"balanced"` | `"balanced"`, `"aggressive"`, or `"high_quality"` |
| `namespace` | str \| None | client default | Target a specific namespace |
| `bits_per_dim` | int \| None | strategy default | Override bits per dimension (2–8) |

```python
savings = client.estimate_savings(strategy="balanced")
# {
#   'namespace': None,
#   'strategy': 'balanced',
#   'bits_per_dim': 4,
#   'original_vectors': 10000,
#   'original_size_mb': 58.6,
#   'compressed_size_mb': 7.3,
#   'savings_pct': 87.5,
#   'compression_ratio': 0.125
# }

# Estimate for a specific namespace
savings = client.estimate_savings(namespace="docs")
```

---

### `compress(...)`

Compress vectors in the index using TurboQuant quantisation.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy` | str | `"balanced"` | `"balanced"`, `"aggressive"`, or `"high_quality"` |
| `dry_run` | bool | `True` | Preview only — no writes |
| `namespace` | str \| None | client default | Target a specific namespace |
| `bits_per_dim` | int \| None | strategy default | Override bits per dimension (2–8) |
| `on_progress` | callable \| None | None | `on_progress(vectors_done, total)` callback |
| `log_path` | str \| None | None | Write JSON log here; `"auto"` → `~/.gilial/logs/<ts>.json` |
| `validate_recall` | bool | `False` | Run recall benchmark before & after (ignored on dry runs) |
| `recall_queries` | list \| None | None | Pre-built query vectors for recall validation |
| `recall_n_queries` | int | `100` | Queries to auto-sample if `recall_queries` is None |
| `recall_k` | int | `10` | Top-k to measure recall over |

**Returns:** `CompressionResult`

```python
# Dry-run preview
preview = client.compress(strategy="balanced", dry_run=True)
print(f"Would save {preview.savings_pct:.1f}%")

# Apply with progress callback
def show_progress(done, total):
    print(f"  {done}/{total} vectors quantised")

result = client.compress(
    strategy="balanced",
    dry_run=False,
    on_progress=show_progress,
    log_path="auto",
)

# Apply to a specific namespace
result = client.compress(namespace="docs", dry_run=False)

# Custom bit depth
result = client.compress(bits_per_dim=3, dry_run=False)

# Apply with built-in recall validation
result = client.compress(
    strategy="balanced",
    dry_run=False,
    validate_recall=True,
    recall_n_queries=200,
    recall_k=10,
)
print(result.recall)
# Recall@10 — 200 queries
#   mean : 98.40%
#   min  : 91.20%
#   max  : 100.00%

if result.recall.safe_to_apply:
    print("Recall within safe bounds (≥95%)")
```

---

### `benchmark(queries, n_queries, k, namespace)`

Run a standalone recall benchmark without compressing anything. Run it twice on an unchanged index (should return ~100%) to confirm the benchmark is working, then use `compress(validate_recall=True)` to measure the real before/after delta.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `queries` | list \| None | None | Pre-built query vectors |
| `n_queries` | int | `100` | Queries to auto-sample |
| `k` | int | `10` | Top-k to measure recall over |
| `namespace` | str \| None | client default | Namespace to query |

**Returns:** `RecallReport`

```python
report = client.benchmark(n_queries=200, k=10)
print(report)
# Recall@10 — 200 queries
#   mean : 100.00%
#   min  : 100.00%
#   max  : 100.00%
#   time : 4.2s

print(report.mean_recall)   # 1.0
print(report.safe_to_apply) # True (mean_recall >= 0.95)
print(report.to_dict())
```

---

### `list_namespaces()`

Return all namespace names in the index.

```python
namespaces = client.list_namespaces()
# ['docs', 'prod', 'staging']
# '' means the default (unnamed) namespace
```

---

### `compress_all_namespaces(...)`

Compress every namespace in one call.

**Parameters:** Same as `compress()`, plus `on_progress(namespace, done, total)`.

**Returns:** `list[CompressionResult]`

```python
results = client.compress_all_namespaces(
    strategy="balanced",
    dry_run=False,
    log_path="auto",
    on_progress=lambda ns, done, total: print(f"{ns}: {done}/{total}"),
)

for r in results:
    print(f"{r.namespace}: saved {r.savings_pct:.1f}%")
```

---

### `get_status()`

Get current index statistics.

```python
status = client.get_status()
print(status["total_vector_count"])
print(status["namespaces"])
```

---

## CompressionResult

| Field | Type | Description |
|-------|------|-------------|
| `strategy` | str | Strategy used |
| `namespace` | str \| None | Namespace targeted |
| `bits_per_dim` | int | Bits per dimension used |
| `dry_run` | bool | Whether this was a preview |
| `original_vectors` | int | Vector count before |
| `compressed_vectors` | int | Vector count after (same for TurboQuant) |
| `original_size_mb` | float | Size before compression |
| `compressed_size_mb` | float | Size after compression |
| `compression_ratio` | float | `compressed / original` |
| `savings_pct` | float | `(1 - ratio) * 100` |
| `duration_seconds` | float | Wall-clock time |
| `recall` | RecallReport \| None | Recall report if `validate_recall=True` |

```python
result.to_dict()  # serialise to plain dict (includes recall)
```

---

## RecallReport

| Field | Type | Description |
|-------|------|-------------|
| `k` | int | Top-k measured |
| `num_queries` | int | Queries run |
| `mean_recall` | float | Average overlap (0–1) |
| `min_recall` | float | Worst-case query recall |
| `max_recall` | float | Best-case query recall |
| `duration_seconds` | float | Time to run both passes |
| `safe_to_apply` | bool | `True` when `mean_recall >= 0.95` |

```python
report.to_dict()   # serialise
str(report)        # human-readable summary
```

---

## Strategies

| Strategy | Bits/dim | Compression ratio | Use case |
|----------|----------|------------------|----------|
| `balanced` | 4 | ~8× | Production default |
| `aggressive` | 2 | ~16× | Maximum savings |
| `high_quality` | 6 | ~5× | Near-lossless |
| custom | 2–8 | varies | `bits_per_dim=N` |

---

## Error Handling

```python
try:
    result = client.compress(dry_run=False)
except ValueError as e:
    print(f"Config error: {e}")
except ConnectionError as e:
    print(f"Could not reach Pinecone: {e}")
except Exception as e:
    print(f"Compression failed: {e}")
```

---

## Complete example

```python
from gilial_code.api.client import PineconeCompressionClient

client = PineconeCompressionClient(
    api_key="pcsk_...",
    index_name="prod-embeddings",
    environment="us-west-1",
)

# 1. Check what's in the index
status = client.get_status()
print(f"Vectors: {status['total_vector_count']}")
print(f"Namespaces: {client.list_namespaces()}")

# 2. Estimate savings
savings = client.estimate_savings()
print(f"Potential savings: {savings['savings_pct']}%")

# 3. Dry-run preview
preview = client.compress(strategy="balanced", dry_run=True)
print(f"Compressed size: {preview.compressed_size_mb} MB")

# 4. Apply with recall validation and logging
result = client.compress(
    strategy="balanced",
    dry_run=False,
    validate_recall=True,
    recall_n_queries=200,
    log_path="auto",
)

print(f"Savings: {result.savings_pct:.1f}%")
print(f"Recall: {result.recall.mean_recall * 100:.1f}%")
print("Safe to keep" if result.recall.safe_to_apply else "Consider reverting")
```
