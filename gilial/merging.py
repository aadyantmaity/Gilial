"""
Phase 3b: Cluster-based memory merging.

Algorithm:
1. Cluster all memories by embedding similarity using HDBSCAN
2. Within each cluster, find pairs above the cosine similarity threshold (~0.92)
3. Merge those near-duplicate pairs: combine content (deduplicated), keep highest importance metadata
4. Write merged memory to DB, delete originals
5. Supports dry_run=True
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from gilial.schema import Memory


@dataclass
class MergeGroup:
    """A set of memories that will be merged into one."""
    members: list[Memory]
    merged: Memory | None = None  # set after merge is performed


@dataclass
class MergingResult:
    merge_groups: list[MergeGroup]   # groups that were merged
    unchanged: list[Memory]          # memories not part of any merge
    dry_run: bool

    def summary(self) -> str:
        mode = "[DRY RUN] " if self.dry_run else ""
        n_merged = sum(len(g.members) for g in self.merge_groups)
        n_new = len(self.merge_groups)
        lines = [
            f"{mode}Merging summary",
            f"  Merge groups : {len(self.merge_groups)}",
            f"  Memories merged (removed): {n_merged}",
            f"  Replacement memories created: {n_new}",
            f"  Unchanged    : {len(self.unchanged)}",
        ]
        for i, g in enumerate(self.merge_groups, 1):
            lines.append(f"  Group {i} ({len(g.members)} members):")
            for m in g.members:
                lines.append(f"    [{m.id[:8]}] score={m.importance_score:.3f} | {m.content[:60]}")
            if g.merged:
                lines.append(f"    → Merged into [{g.merged.id[:8]}]: {g.merged.content[:60]}")
        return "\n".join(lines)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def run_merging(
    memories: list[Memory],
    db,
    writer,
    similarity_threshold: float = 0.92,
    min_cluster_size: int = 2,
    dry_run: bool = True,
    log_path: str = "./merge_log.jsonl",
) -> MergingResult:
    """
    Cluster memories and merge near-duplicates above similarity_threshold.

    Args:
        memories: all memories with embeddings
        db: ChromaDB instance
        writer: MemoryWriter instance (used to store merged memory)
        similarity_threshold: cosine similarity above which two memories are near-duplicates
        min_cluster_size: minimum cluster size for HDBSCAN
        dry_run: if True, do not modify DB
        log_path: where to write merge log
    """
    if len(memories) < 2:
        return MergingResult(merge_groups=[], unchanged=list(memories), dry_run=dry_run)

    # Step 1: cluster with HDBSCAN
    clusters = _cluster(memories, min_cluster_size=min_cluster_size)

    # Step 2: within each cluster, find merge groups above threshold
    merge_groups: list[MergeGroup] = []
    merged_ids: set[str] = set()

    for cluster_members in clusters.values():
        if len(cluster_members) < 2:
            continue
        groups = _find_merge_groups(cluster_members, similarity_threshold)
        merge_groups.extend(groups)
        for g in groups:
            for m in g.members:
                merged_ids.add(m.id)

    unchanged = [m for m in memories if m.id not in merged_ids]

    # Step 3: perform merges
    _log_merges(merge_groups, dry_run=dry_run, log_path=log_path)

    if not dry_run:
        for group in merge_groups:
            merged_memory = _merge_memories(group.members, writer)
            group.merged = merged_memory
            for m in group.members:
                db.delete(m.id)

    return MergingResult(merge_groups=merge_groups, unchanged=unchanged, dry_run=dry_run)


def _cluster(memories: list[Memory], min_cluster_size: int = 2) -> dict[int, list[Memory]]:
    """Run HDBSCAN on embeddings. Returns {cluster_label: [Memory, ...]}. Label -1 = noise."""
    try:
        import hdbscan
    except ImportError:
        raise ImportError("Install hdbscan: pip install hdbscan")

    embeddings = np.array([m.embedding for m in memories], dtype=np.float32)
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric="euclidean",
    )
    labels = clusterer.fit_predict(embeddings)

    clusters: dict[int, list[Memory]] = {}
    for memory, label in zip(memories, labels):
        clusters.setdefault(int(label), []).append(memory)
    return clusters


def _find_merge_groups(members: list[Memory], threshold: float) -> list[MergeGroup]:
    """Within a cluster, group memories whose pairwise cosine similarity >= threshold."""
    # Union-find to group near-duplicates
    parent = {m.id: m.id for m in members}
    id_to_memory = {m.id: m for m in members}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    for i, a in enumerate(members):
        for b in members[i + 1:]:
            if cosine_similarity(a.embedding, b.embedding) >= threshold:
                union(a.id, b.id)

    # Group by root
    groups: dict[str, list[Memory]] = {}
    for m in members:
        root = find(m.id)
        groups.setdefault(root, []).append(m)

    return [MergeGroup(members=g) for g in groups.values() if len(g) >= 2]


def _merge_memories(members: list[Memory], writer) -> Memory:
    """
    Merge a group of near-duplicate memories into one.
    - Content: join unique sentences from all members
    - Metadata: take max importance_score, sum access_counts, union tags
    - Embedding: re-embed the merged content
    """
    # Deduplicate content at sentence level
    seen: set[str] = set()
    sentences: list[str] = []
    for m in members:
        for sentence in m.content.replace(".", ".\n").splitlines():
            s = sentence.strip()
            if s and s not in seen:
                seen.add(s)
                sentences.append(s)
    merged_content = " ".join(sentences)

    # Preserve best metadata
    best_importance = max(m.importance_score for m in members)
    total_access = sum(m.access_count for m in members)
    all_tags = list({tag for m in members for tag in m.tags})

    merged = writer.store(
        merged_content,
        tags=all_tags,
        importance_score=best_importance,
    )
    merged.access_count = total_access
    writer.db.update_metadata(merged)
    return merged


def _log_merges(groups: list[MergeGroup], dry_run: bool, log_path: str):
    if not groups:
        return
    path = Path(log_path)
    with open(path, "a") as f:
        for group in groups:
            entry = {
                "event": "dry_run_merge" if dry_run else "merge",
                "member_ids": [m.id for m in group.members],
                "member_previews": [m.content[:80] for m in group.members],
                "member_scores": [m.importance_score for m in group.members],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            f.write(json.dumps(entry) + "\n")
