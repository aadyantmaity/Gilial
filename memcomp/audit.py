from __future__ import annotations

from dataclasses import dataclass

from memcomp.schema import Memory


@dataclass
class AuditDiff:
    deleted_memories: list[Memory]
    added_memories: list[Memory]
    retained_memories: list[Memory]
    summary: str


class CompressionAudit:
    def diff(self, before_ids: list[str], after_ids: list[str], writer) -> AuditDiff:
        before_set = set(before_ids)
        after_set = set(after_ids)

        deleted_ids = before_set - after_set
        added_ids = after_set - before_set
        retained_ids = before_set & after_set

        deleted = [m for mid in deleted_ids if (m := writer.db.get_by_id(mid)) is not None]
        # deleted memories may already be gone from DB; fall back to empty Memory stubs
        # by fetching from writer which might not have them — collect what we can
        added = [m for mid in added_ids if (m := writer.db.get_by_id(mid)) is not None]
        retained = [m for mid in retained_ids if (m := writer.db.get_by_id(mid)) is not None]

        summary = f"{len(deleted_ids)} deleted, {len(added_ids)} added, {len(retained_ids)} retained"
        return AuditDiff(
            deleted_memories=deleted,
            added_memories=added,
            retained_memories=retained,
            summary=summary,
        )

    def format_diff(self, diff: AuditDiff) -> str:
        lines = [f"Compression Diff — {diff.summary}", ""]

        def _preview(memories: list[Memory], label: str) -> list[str]:
            if not memories:
                return []
            out = [f"=== {label} ({len(memories)}) ==="]
            for m in memories:
                preview = m.content[:80] + ("…" if len(m.content) > 80 else "")
                out.append(f"  [{m.id[:8]}] {preview}")
            return out

        lines += _preview(diff.deleted_memories, "DELETED")
        lines += _preview(diff.added_memories, "ADDED")
        lines += _preview(diff.retained_memories, "RETAINED")
        return "\n".join(lines)
