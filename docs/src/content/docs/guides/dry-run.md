---
title: Using Dry-Run Mode
description: Preview compression without making changes
---
Dry-run mode lets you preview compression impact **without making any changes** to your index.

## What is Dry-Run?

When you set `dry_run=True`, Gilial:
- Analyzes your vectors
- Calculates which vectors would be deleted
- Reports estimated savings
- **Does NOT** delete anything

## Basic Usage

```bash
curl -X POST http://localhost:8000/compress \
  -H "Content-Type: application/json" \
  -d '{"strategy": "balanced", "dry_run": true}'
```

## Understanding the Results

The response includes:

```json
{
  "original_vectors": 10000,
  "compressed_vectors": 9739,
  "original_size_mb": 29.30,
  "compressed_size_mb": 28.53,
  "compression_ratio": 0.974,
  "savings_pct": 2.61
}
```

- **original_vectors** - Starting vector count
- **compressed_vectors** - Vectors after compression
- **savings_pct** - Percentage of space saved
- **compression_ratio** - New size / original size

## Workflow Example

```bash
# Step 1: Estimate savings
curl http://localhost:8000/estimate?strategy=balanced

# Step 2: Dry-run to confirm
curl -X POST http://localhost:8000/compress \
  -H "Content-Type: application/json" \
  -d '{"strategy": "balanced", "dry_run": true}'

# Step 3: Apply if happy (if savings > 2%)
curl -X POST http://localhost:8000/compress \
  -H "Content-Type: application/json" \
  -d '{"strategy": "balanced", "dry_run": false}'
```

## Best Practices

1. **Always dry-run first** - Never jump to `dry_run=False`
2. **Review the numbers** - Check if savings justify the deletion
3. **Use for testing** - Test compression strategies on a copy before applying
4. **Monitor queries** - Run dry-run before and after to spot impact
5. **Document changes** - Keep records of compression runs

## Common Dry-Run Patterns

### Check Before Every Compression

Always dry-run first before applying:

```bash
# Dry-run
curl -X POST http://localhost:8000/compress \
  -d '{"strategy": "balanced", "dry_run": true}' | jq '.savings_pct'

# Only apply if savings look good
curl -X POST http://localhost:8000/compress \
  -d '{"strategy": "balanced", "dry_run": false}'
```

### Compare Strategies

Test both strategies to see which gives better results:

```bash
# Test balanced
curl -X POST http://localhost:8000/compress \
  -d '{"strategy": "balanced", "dry_run": true}' | jq '.savings_pct'

# Test aggressive
curl -X POST http://localhost:8000/compress \
  -d '{"strategy": "aggressive", "dry_run": true}' | jq '.savings_pct'
```
