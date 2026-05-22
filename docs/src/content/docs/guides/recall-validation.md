---
title: Recall Validation
description: Benchmark top-k overlap before and after compression
---

Recall validation is how you confirm that compression didn't meaningfully change what your index returns. Gilial measures this by running the same set of query vectors against the index before and after quantisation, then computing what fraction of the original top-k results still appear in the new top-k.

A result of 98.4% means that across all your benchmark queries, on average 9.84 out of 10 original results still appear after compression.

---

## Built into `compress()`

Pass `validate_recall=True` to run the benchmark automatically as part of a live compression:

```python
result = client.compress(
    strategy="balanced",
    dry_run=False,
    validate_recall=True,
    recall_n_queries=200,   # how many query vectors to sample
    recall_k=10,            # measure recall@10
)

print(result.recall)
# Recall@10 — 200 queries
#   mean : 98.40%
#   min  : 91.20%
#   max  : 100.00%
#   time : 6.3s

if result.recall.safe_to_apply:
    print("Within safe bounds — mean recall ≥ 95%")
else:
    print("Recall dropped below 95% — consider a lighter strategy")
```

The `recall` field on `CompressionResult` is a `RecallReport`. It is `None` on dry runs.

---

## Standalone benchmark

Run `benchmark()` on an unchanged index to establish a baseline. It queries the index twice with the same vectors — the result should be ~100%.

```python
report = client.benchmark(n_queries=200, k=10)
print(report)
# Recall@10 — 200 queries
#   mean : 100.00%
#   min  : 100.00%
#   max  : 100.00%
#   time : 4.2s
```

If this returns significantly below 100%, your index may be non-deterministic (e.g. approximate search with high variability). Factor that in when interpreting post-compression recall.

---

## Bring your own queries

If you have a curated set of representative query vectors (e.g. from your production query logs), pass them directly:

```python
my_queries = [
    [0.12, -0.34, ...],   # 1536-d float list
    ...
]

result = client.compress(
    strategy="balanced",
    dry_run=False,
    validate_recall=True,
    recall_queries=my_queries,
    recall_k=10,
)
```

Using real query traffic as the benchmark set is the most accurate signal — it measures recall on the actual distribution your users produce, not a random sample.

---

## RecallReport reference

| Field | Type | Description |
|-------|------|-------------|
| `k` | int | Top-k measured |
| `num_queries` | int | Number of queries run |
| `mean_recall` | float | Average overlap (0–1) |
| `min_recall` | float | Worst single-query recall |
| `max_recall` | float | Best single-query recall |
| `per_query_recall` | list[float] | Per-query breakdown |
| `duration_seconds` | float | Total benchmark time |
| `safe_to_apply` | bool | `True` when `mean_recall ≥ 0.95` |

```python
report.to_dict()    # serialise to plain dict
str(report)         # human-readable summary
```

---

## What counts as safe?

`safe_to_apply` uses a fixed 95% threshold. You may want a stricter bar for critical indexes:

```python
# Require 99% mean recall for production
if result.recall.mean_recall >= 0.99:
    print("Safe for production")
elif result.recall.mean_recall >= 0.95:
    print("Acceptable — monitor closely")
else:
    print("Too much recall loss — use a lighter strategy")
```

Also inspect `min_recall`. A mean of 98% with a worst-case query of 60% may indicate a cluster of vectors that compress poorly.

---

## Including recall in logs

When using `log_path`, the recall report is included automatically:

```python
result = client.compress(
    strategy="balanced",
    dry_run=False,
    validate_recall=True,
    log_path="auto",   # writes to ~/.gilial/logs/<timestamp>.json
)
```

The log includes `result.recall.to_dict()` nested under `result.recall`.
