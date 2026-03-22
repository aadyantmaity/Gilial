"""
Phase 3c: LLM-based summarization for related memory clusters.

Algorithm:
1. Cluster all memories with HDBSCAN
2. Within each cluster, find groups in the 0.75-0.92 cosine similarity range
   (above 0.92 is merging territory; below 0.75 is too dissimilar to summarize)
3. Send each group to an LLM to produce a summary
4. Store the summary as a new memory with averaged importance + union tags
5. Delete source memories after summary is stored
6. Supports dry_run=True
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from memcomp.schema import Memory
from memcomp.merging import cosine_similarity, _cluster


@dataclass
class SummaryGroup:
    members: list[Memory]
    summary: Memory | None = None     # set after summarization runs
    summary_text: str = ""            # the LLM-generated summary text


@dataclass
class SummarizationResult:
    summary_groups: list[SummaryGroup]
    unchanged: list[Memory]
    dry_run: bool

    def summary(self) -> str:
        mode = "[DRY RUN] " if self.dry_run else ""
        n_summarized = sum(len(g.members) for g in self.summary_groups)
        lines = [
            f"{mode}Summarization summary",
            f"  Summary groups  : {len(self.summary_groups)}",
            f"  Memories summarized (removed): {n_summarized}",
            f"  Replacements created: {len(self.summary_groups)}",
            f"  Unchanged       : {len(self.unchanged)}",
        ]
        for i, g in enumerate(self.summary_groups, 1):
            lines.append(f"  Group {i} ({len(g.members)} members):")
            for m in g.members:
                lines.append(f"    [{m.id[:8]}] score={m.importance_score:.3f} | {m.content[:60]}")
            if g.summary_text:
                lines.append(f"    -> Summary: {g.summary_text[:80]}")
        return "\n".join(lines)


def run_summarization(
    memories: list[Memory],
    db,
    writer,
    llm_fn,                             # callable(texts: list[str]) -> str
    low_threshold: float = 0.75,
    high_threshold: float = 0.92,
    min_cluster_size: int = 2,
    dry_run: bool = True,
    log_path: str = "./summarization_log.jsonl",
) -> SummarizationResult:
    """
    Summarize clusters of related (but not near-duplicate) memories.

    Args:
        memories: all memories with embeddings
        db: ChromaDB instance
        writer: MemoryWriter instance
        llm_fn: callable that takes a list of memory content strings and returns a summary string
        low_threshold: minimum cosine similarity to be summarization candidate
        high_threshold: maximum cosine similarity (above this is merging territory)
        min_cluster_size: minimum cluster size for HDBSCAN
        dry_run: if True, generate summaries but do not modify DB
        log_path: where to write summarization log
    """
    if len(memories) < 2:
        return SummarizationResult(summary_groups=[], unchanged=list(memories), dry_run=dry_run)

    # Step 1: cluster with HDBSCAN
    clusters = _cluster(memories, min_cluster_size=min_cluster_size)

    # Step 2: find summarization groups within each cluster
    summary_groups: list[SummaryGroup] = []
    summarized_ids: set[str] = set()

    for cluster_members in clusters.values():
        if len(cluster_members) < 2:
            continue
        groups = _find_summary_groups(cluster_members, low_threshold, high_threshold)
        summary_groups.extend(groups)
        for g in groups:
            for m in g.members:
                summarized_ids.add(m.id)

    unchanged = [m for m in memories if m.id not in summarized_ids]

    # Step 3: generate summaries
    for group in summary_groups:
        group.summary_text = llm_fn([m.content for m in group.members])

    # Step 4: log
    _log_summaries(summary_groups, dry_run=dry_run, log_path=log_path)

    # Step 5: store summaries and delete sources (if not dry run)
    if not dry_run:
        for group in summary_groups:
            max_importance = max(m.importance_score for m in group.members)
            total_access = sum(m.access_count for m in group.members)
            all_tags = list({tag for m in group.members for tag in m.tags})

            # Store summary -- use max importance so the summary isn't penalized
            summary_mem = writer.store(
                group.summary_text,
                tags=all_tags,
                importance_score=max_importance,
            )
            summary_mem.access_count = total_access
            writer.db.update_metadata(summary_mem)
            group.summary = summary_mem

            # Delete sources
            for m in group.members:
                db.delete(m.id)

    return SummarizationResult(summary_groups=summary_groups, unchanged=unchanged, dry_run=dry_run)


def _find_summary_groups(
    members: list[Memory],
    low_threshold: float,
    high_threshold: float,
) -> list[SummaryGroup]:
    """
    Group memories whose pairwise cosine similarity is in [low_threshold, high_threshold).
    Uses union-find -- same approach as merging but with a different threshold band.
    """
    parent = {m.id: m.id for m in members}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    for i, a in enumerate(members):
        for b in members[i + 1:]:
            sim = cosine_similarity(a.embedding, b.embedding)
            if low_threshold <= sim < high_threshold:
                union(a.id, b.id)

    groups: dict[str, list[Memory]] = {}
    for m in members:
        root = find(m.id)
        groups.setdefault(root, []).append(m)

    return [SummaryGroup(members=g) for g in groups.values() if len(g) >= 2]


def make_llm_fn(writer) -> callable:
    """
    Build a default llm_fn using the sentence-transformers model for extractive summarization.

    Since sentence-transformers doesn't generate text, this uses a simple extractive approach:
    pick the sentence from all members that is most central (highest avg similarity to others).
    For real abstractive summarization, replace this with an LLM call (e.g. via OpenRouter).
    """
    def _extractive_summarize(texts: list[str]) -> str:
        if len(texts) == 1:
            return texts[0]
        # Embed all texts
        embeddings = [writer.embed(t) for t in texts]
        vecs = [np.array(e) for e in embeddings]
        # Score each by avg cosine similarity to all others
        best_idx, best_score = 0, -1.0
        for i, vi in enumerate(vecs):
            others = [vecs[j] for j in range(len(vecs)) if j != i]
            avg_sim = np.mean([
                float(np.dot(vi, vj) / (np.linalg.norm(vi) * np.linalg.norm(vj) + 1e-9))
                for vj in others
            ])
            if avg_sim > best_score:
                best_score = avg_sim
                best_idx = i
        # Combine: lead with the most central sentence, append unique content from others
        seen = set(texts[best_idx].split())
        extra = []
        for i, t in enumerate(texts):
            if i == best_idx:
                continue
            new_words = [w for w in t.split() if w not in seen]
            if len(new_words) > len(t.split()) * 0.4:  # at least 40% new content
                extra.append(t)
                seen.update(new_words)
        parts = [texts[best_idx]] + extra
        return " | ".join(parts)

    return _extractive_summarize


def _log_summaries(groups: list[SummaryGroup], dry_run: bool, log_path: str):
    if not groups:
        return
    path = Path(log_path)
    with open(path, "a") as f:
        for group in groups:
            entry = {
                "event": "dry_run_summarize" if dry_run else "summarize",
                "member_ids": [m.id for m in group.members],
                "member_previews": [m.content[:80] for m in group.members],
                "summary_text": group.summary_text[:200],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            f.write(json.dumps(entry) + "\n")
