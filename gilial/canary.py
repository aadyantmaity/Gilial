from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CanaryVerificationResult:
    survived: list[str]
    lost: list[str]
    survival_rate: float
    passed: bool


class CanarySet:
    def __init__(self):
        self._canary_ids: list[str] = []

    def inject(self, writer, canaries: list[dict]) -> list[str]:
        ids = []
        for c in canaries:
            tags = list(c.get("tags", []))
            if "canary" not in tags:
                tags.append("canary")
            memory = writer.store(content=c["content"], tags=tags)
            ids.append(memory.id)
        self._canary_ids.extend(ids)
        return ids

    def verify(self, writer) -> CanaryVerificationResult:
        all_ids = {m.id for m in writer.db.get_all()}
        survived = [cid for cid in self._canary_ids if cid in all_ids]
        lost = [cid for cid in self._canary_ids if cid not in all_ids]
        total = len(self._canary_ids)
        survival_rate = len(survived) / total if total > 0 else 1.0
        return CanaryVerificationResult(
            survived=survived,
            lost=lost,
            survival_rate=survival_rate,
            passed=survival_rate == 1.0,
        )
