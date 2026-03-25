---
title: Compression Strategies
description: Learn about Balanced and Aggressive strategies
---

Gilial offers different compression strategies to match your needs.

## Balanced (Default)

The safest option for most use cases.

**Characteristics:**
- Retention rate: 72.8%
- Vectors removed: ~27.2%
- Ideal for: Production environments, safety-first approach

**When to use:**
- You want predictable, moderate compression
- Data integrity is important
- You need good balance between space savings and quality

```python
client.compress(strategy="balanced", dry_run=False)
```

## Aggressive

Maximum compression for space-critical scenarios.

**Characteristics:**
- Retention rate: 67%
- Vectors removed: ~33%
- Ideal for: Cost optimization, non-critical indexes

**When to use:**
- Storage costs are critical
- You can afford minor quality loss
- You have backups and can re-compress if needed

```python
client.compress(strategy="aggressive", dry_run=False)
```

## How Scoring Works

Both strategies use **L2 norm** (Euclidean magnitude) to score vectors:

```
score = sqrt(v₁² + v₂² + ... + v₇₆₈²)
```

Higher norms = higher quality vectors
Lower norms = candidates for deletion

## Dry-Run First!

Always preview compression with `dry_run=True`:

```python
# Preview changes
preview = client.compress(strategy="balanced", dry_run=True)
print(f"Would delete: {preview.metadata['deleted_vectors']} vectors")

# If happy with preview, apply:
result = client.compress(strategy="balanced", dry_run=False)
```

## Recommendations

1. **Start with Balanced** - It's proven and safe
2. **Test on non-critical index first** - Understand the impact
3. **Always use dry-run** - Preview before applying
4. **Maintain backups** - Have a recovery plan
5. **Monitor metrics** - Track query latency before/after
