---
title: Best Practices
description: Guidelines for safe and effective compression
---

Follow these guidelines to get the most out of Gilial.

## Before Compression

### 1. Estimate first

Always run `estimate_savings()` before touching the index. The ratio is deterministic so this is free — no vectors are fetched.

```python
savings = client.estimate_savings(strategy="balanced")
print(f"Potential savings: {savings['savings_pct']}%")
```

### 2. Dry-run before applying

```python
preview = client.compress(strategy="balanced", dry_run=True)
print(f"Compressed size: {preview.compressed_size_mb} MB")
```

### 3. Validate recall before committing

Use `validate_recall=True` to run a before/after benchmark automatically. Gilial will sample query vectors from the index, record top-k results, run compression, re-query, and report overlap.

```python
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
#   ...

if not result.recall.safe_to_apply:
    print("Recall dropped below 95% — consider reverting or using a lighter strategy")
```

`recall.safe_to_apply` is `True` when mean recall ≥ 95%. For critical production indexes you may want to raise that bar by inspecting `mean_recall` directly.

### 4. Run a standalone benchmark first

Before your first compression, run `benchmark()` on the unchanged index to confirm your baseline. It should return ~100% recall (querying twice with the same vectors).

```python
baseline = client.benchmark(n_queries=200, k=10)
print(baseline)  # should show mean: 100.00%
```

### 5. Start with Balanced, graduate to Aggressive

- **Balanced** (4-bit, ~8×) is the safe default for production
- **Aggressive** (2-bit, ~16×) maximises savings but shifts vectors further
- **high_quality** (6-bit, ~5×) is near-lossless for sensitive indexes

### 6. Use namespace targeting for staged rollouts

Compress a low-traffic namespace first, validate recall, then move to higher-traffic ones.

```python
namespaces = client.list_namespaces()
print(namespaces)  # ['staging', 'docs', 'prod']

# Start with staging
result = client.compress(namespace="staging", dry_run=False, validate_recall=True)
if result.recall.safe_to_apply:
    client.compress(namespace="prod", dry_run=False, validate_recall=True)
```

### 7. Log every compression run

Pass `log_path="auto"` to write a timestamped JSON record to `~/.gilial/logs/`. The log includes compression stats and the full recall report.

```python
result = client.compress(
    strategy="balanced",
    dry_run=False,
    log_path="auto",
    validate_recall=True,
)
```

---

## During Compression

### Track progress on large indexes

```python
def on_progress(done, total):
    pct = done / total * 100
    print(f"\r  {done}/{total} ({pct:.1f}%)", end="", flush=True)

client.compress(strategy="balanced", dry_run=False, on_progress=on_progress)
```

### Use custom bit depth for fine control

Instead of a named strategy, dial in the exact bit depth:

```python
# Something between balanced (4-bit) and high_quality (6-bit)
result = client.compress(bits_per_dim=5, dry_run=False)
```

---

## After Compression

### Verify index health

```python
status = client.get_status()
print(f"Vectors: {status['total_vector_count']}")
```

### Review the recall report

If `validate_recall=True` was used, inspect `result.recall`:

```python
print(f"Mean recall: {result.recall.mean_recall * 100:.2f}%")
print(f"Worst query: {result.recall.min_recall * 100:.2f}%")
```

A mean recall above 98% is excellent. Below 95% warrants review.

---

## Do's and Don'ts

### ✅ Do
- Always estimate and dry-run first
- Use `validate_recall=True` before hitting apply on production
- Target namespaces individually for staged rollouts
- Log every run with `log_path="auto"`
- Start with Balanced, move to Aggressive only after validating recall

### ❌ Don't
- Skip dry-run mode
- Use Aggressive strategy on production without a recall check
- Ignore `recall.min_recall` — a single catastrophically bad query matters
- Compress the same index repeatedly in a short window

---

## Recommended schedule

| Cadence | Action |
|---------|--------|
| Weekly | Check index growth with `get_status()` |
| Monthly | Run `estimate_savings()` dry-run |
| Quarterly | Apply compression if savings > 5%, with `validate_recall=True` |

Adjust based on your vector accumulation rate.
