---
title: Introduction to Gilial
description: Get started with Gilial vector compression
---

# Introduction to Gilial

Gilial is an intelligent vector compression system for Pinecone indexes. It helps you reduce storage costs and improve query performance by removing low-scoring vectors while maintaining search quality.

## What is Vector Compression?

Vector databases like Pinecone can grow unbounded as you add more embeddings. Over time, your index accumulates:
- Low-quality vectors that don't contribute to search relevance
- Redundant or duplicate vectors
- Outdated vectors that are no longer needed

Gilial solves this by analyzing your vectors and intelligently removing the lowest-scoring ones based on L2 norm calculations.

## Why Use Gilial?

### Cost Savings
- Reduce storage costs by removing unnecessary vectors
- Lower API costs through smaller index sizes
- Decrease bandwidth requirements for index transfers

### Performance Improvements
- Faster nearest-neighbor searches with smaller datasets
- Improved cache hit rates
- Lower query latency

### Simple and Safe
- Dry-run mode lets you preview changes before applying
- Multiple compression strategies (Balanced, Aggressive)
- Clear metrics on impact and savings

## How It Works

1. **Sample** - Connect to your Pinecone index and sample vectors
2. **Score** - Calculate L2 norm for each vector to determine quality
3. **Delete** - Remove low-scoring vectors based on your chosen strategy

The process is fast, deterministic, and reversible (with backups).

## Getting Started

Ready to compress your vector database? Follow the [Installation Guide](./installation.md) to get started.
