---
title: Compression Strategies
description: Learn about Balanced, Aggressive, High-Quality and custom strategies
---

Gilial compresses vectors using **TurboQuant** — a random-rotation scalar quantisation algorithm. Instead of deleting vectors, it reduces each vector's storage footprint by lowering the number of bits used per dimension. All vectors are retained; only their precision changes.

## Named Strategies

### Balanced (default)

4 bits per dimension, ~8× compression. The safe production default.

```python
result = client.compress(strategy="balanced", dry_run=False)
```

| Property | Value |
|----------|-------|
| Bits/dim | 4 |
| Compression ratio | ~8× |
| Typical recall@10 | ≥ 98% |
| Use case | Production, safety-first |

### Aggressive

2 bits per dimension, ~16× compression. Maximum savings.

```python
result = client.compress(strategy="aggressive", dry_run=False)
```

| Property | Value |
|----------|-------|
| Bits/dim | 2 |
| Compression ratio | ~16× |
| Typical recall@10 | ≥ 93% |
| Use case | Cost optimisation, non-critical indexes |

Always validate recall when using Aggressive on production:

```python
result = client.compress(
    strategy="aggressive",
    dry_run=False,
    validate_recall=True,
    recall_n_queries=200,
)
print(result.recall)
```

### High Quality

6 bits per dimension, ~5× compression. Near-lossless.

```python
result = client.compress(strategy="high_quality", dry_run=False)
```

| Property | Value |
|----------|-------|
| Bits/dim | 6 |
| Compression ratio | ~5× |
| Typical recall@10 | ≥ 99.5% |
| Use case | Sensitive indexes, fine-tuned models |

---

## Custom Bit Depth

Override the strategy default with `bits_per_dim` (2–8). Useful when you want something between two named strategies.

```python
# Between balanced (4) and high_quality (6)
result = client.compress(bits_per_dim=5, dry_run=False)

# Or combine with a named strategy as a starting point
result = client.compress(strategy="aggressive", bits_per_dim=3, dry_run=False)
```

---

## How TurboQuant Works

1. **Random rotation** — vectors are multiplied by a seeded random orthogonal matrix, spreading energy evenly across dimensions
2. **Scalar quantisation** — each rotated dimension is quantised to N bits
3. **Optional QJL correction** — a 1-bit residual stage (enabled by default on Balanced and High Quality) improves reconstruction accuracy
4. **Decode to float32** — vectors are decoded back before upserting so the index stays compatible with existing query infrastructure

The precision loss from quantisation is the compression mechanism. No vectors are deleted.

---

## Choosing a Strategy

```
Need maximum savings and can tolerate minor quality loss?
  → aggressive (2-bit)

Running production queries where quality matters most?
  → high_quality (6-bit)

Everything else?
  → balanced (4-bit)  ← start here

Want fine-grained control?
  → bits_per_dim=N
```

Always use `validate_recall=True` before committing to aggressive quantisation on a production index.
