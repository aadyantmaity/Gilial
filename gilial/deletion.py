"""
Phase 3a: Threshold-based memory deletion.

Rules:
- Drop memories whose importance_score is below `score_floor`
- Safeguard: never delete the top `protect_top_pct` percent by importance score
- Supports dry_run=True to log what WOULD be deleted without touching the DB
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from gilial.schema import Memory


@dataclass
class DeletionResult:
    deleted: list[Memory]       # memories actually deleted (or would-be in dry_run)
    protected: list[Memory]     # memories kept due to top-N% safeguard
    kept: list[Memory]          # memories kept because score >= floor
    dry_run: bool

    def summary(self) -> str:
        mode = "[DRY RUN] " if self.dry_run else ""
        lines = [
            f"{mode}Deletion summary",
            f"  Deleted  : {len(self.deleted)}",
            f"  Protected: {len(self.protected)} (top-N% safeguard)",
            f"  Kept     : {len(self.kept)} (score above floor)",
        ]
        if self.deleted:
            lines.append("  Deleted memories:")
            for m in self.deleted:
                lines.append(f"    [{m.id[:8]}] score={m.importance_score:.3f} | {m.content[:60]}")
        return "\n".join(lines)


def run_deletion(
    memories: list[Memory],
    db,                          # ChromaDB instance
    score_floor: float = 0.2,
    protect_top_pct: float = 0.2,
    dry_run: bool = True,
    log_path: str = "./deletion_log.jsonl",
) -> DeletionResult:
    """
    Delete memories below score_floor, but never the top protect_top_pct.

    Args:
        memories: all memories in the store (with importance_score already set)
        db: ChromaDB instance for actual deletions
        score_floor: memories with importance_score below this are candidates
        protect_top_pct: fraction of memories always kept (e.g. 0.2 = top 20%)
        dry_run: if True, log only — do not delete
        log_path: where to write the deletion log

    Returns:
        DeletionResult with deleted/protected/kept lists
    """
    if not memories:
        return DeletionResult(deleted=[], protected=[], kept=[], dry_run=dry_run)

    # Sort descending by importance score
    ranked = sorted(memories, key=lambda m: m.importance_score, reverse=True)

    # How many to protect
    n_protect = max(1, int(len(ranked) * protect_top_pct))
    protected_ids = {m.id for m in ranked[:n_protect]}

    deleted, protected, kept = [], [], []

    for m in ranked:
        if m.id in protected_ids:
            protected.append(m)
        elif m.importance_score < score_floor:
            deleted.append(m)
        else:
            kept.append(m)

    # Perform deletion (or log intent)
    _log_deletion(deleted, dry_run=dry_run, log_path=log_path)

    if not dry_run:
        for m in deleted:
            db.delete(m.id)

    return DeletionResult(deleted=deleted, protected=protected, kept=kept, dry_run=dry_run)


def _log_deletion(memories: list[Memory], dry_run: bool, log_path: str):
    """Append one JSONL entry per deleted memory."""
    if not memories:
        return
    path = Path(log_path)
    with open(path, "a") as f:
        for m in memories:
            entry = {
                "event": "dry_run_delete" if dry_run else "delete",
                "memory_id": m.id,
                "content_preview": m.content[:80],
                "importance_score": m.importance_score,
                "access_count": m.access_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            f.write(json.dumps(entry) + "\n")
