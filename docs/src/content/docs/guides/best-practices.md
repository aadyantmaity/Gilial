---
title: Best Practices
description: Guidelines for safe and effective compression
---

Follow these guidelines to get the most out of Gilial.

## Before Compression

### 1. Backup Your Index
Always create a backup before compressing:

```bash
# With Pinecone CLI or console
# Create a snapshot or export your index data
```

### 2. Test on a Copy
If possible, test compression on a copy of your index first.

### 3. Schedule Off-Peak
Run compression during off-peak hours:
- Lower query load
- Less disruption
- Easier to rollback if needed

### 4. Understand Your Data
- What vectors do you have?
- How old is your oldest vector?
- What's your typical query pattern?

## During Compression

### 1. Use Dry-Run First
```python
# Always preview
preview = client.compress(strategy="balanced", dry_run=True)
print(f"Would save: {preview.savings_pct}%")

# Then apply
result = client.compress(strategy="balanced", dry_run=False)
```

### 2. Start Conservative
- Begin with **Balanced** strategy
- Graduate to **Aggressive** after you're comfortable

### 3. Monitor Progress
- Check compression status
- Watch for any errors
- Keep logs for reference

## After Compression

### 1. Verify Results
```python
# Check new index size
status = client.get_status()
print(f"New vector count: {status['total_vector_count']}")
```

### 2. Test Query Performance
- Run sample queries before and after
- Measure query latency
- Check relevance of results

### 3. Monitor Metrics
Track over time:
- Storage usage
- Query latency
- Index size
- Cost trends

## Do's and Don'ts

### ✅ Do
- Always use dry-run first
- Maintain backups
- Test on non-critical indexes
- Run during off-peak hours
- Start with Balanced strategy
- Document compression runs
- Monitor query performance

### ❌ Don't
- Skip dry-run mode
- Compress production without backup
- Use Aggressive on critical data
- Ignore query latency changes
- Compress frequently (vectors need time to accumulate)
- Forget to verify results

## Troubleshooting

### Compression is Too Slow
- It's normal for large indexes (10k+ vectors)
- Consider compressing during off-peak hours
- Break into smaller batches if needed

### Savings Are Too Low
- Your index may be well-optimized already
- Try again after accumulating more vectors
- Consider Aggressive strategy if safe to do

### Query Quality Decreased
- Revert to previous backup
- Use more conservative strategy next time
- Consider compression less frequently

## Recommended Schedule

- **Weekly** - Monitor index growth
- **Monthly** - Run dry-run analysis
- **Quarterly** - Apply compression if savings > 2%
- **Yearly** - Review compression strategy

Adjust based on your vector accumulation rate and budget.
