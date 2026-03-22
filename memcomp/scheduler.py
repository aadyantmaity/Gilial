from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from memcomp.writer import MemoryWriter

logger = logging.getLogger(__name__)


@dataclass
class CompressionLog:
    path: Path = field(default_factory=lambda: Path("compression_log.jsonl"))

    def append(self, entry: dict):
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")


class CompressionScheduler:
    def __init__(
        self,
        writer: MemoryWriter,
        interval_hours: float | None = None,
        size_threshold: int | None = None,
        dry_run: bool = True,
    ):
        self._writer = writer
        self._interval_hours = interval_hours
        self._size_threshold = size_threshold
        self._dry_run = dry_run

        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._last_run_time: str | None = None
        self._last_run_result: dict | None = None
        self._log = CompressionLog()
        self._snapshots_dir = Path("snapshots")

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join()
            self._thread = None

    def run_now(self, reason: str = "manual") -> dict:
        return self._run_cycle(reason)

    def status(self) -> dict:
        with self._lock:
            return {
                "is_running": self._thread is not None and self._thread.is_alive(),
                "last_run_time": self._last_run_time,
                "last_run_result": self._last_run_result,
                "snapshots_available": self._list_snapshots(),
            }

    def rollback(self, snapshot_id: str):
        snapshot_path = self._snapshots_dir / f"{snapshot_id}.json"
        if not snapshot_path.exists():
            logger.error("Snapshot %s not found", snapshot_id)
            return
        with open(snapshot_path) as f:
            data = json.load(f)
        logger.info(
            "Rollback requested for snapshot %s. Would restore %d memory IDs: %s",
            snapshot_id,
            len(data["memory_ids"]),
            data["memory_ids"],
        )

    # -- internal --

    def _loop(self):
        last_interval_check = time.monotonic()
        while not self._stop_event.is_set():
            triggered = False
            reason = ""

            if self._interval_hours is not None:
                elapsed = time.monotonic() - last_interval_check
                if elapsed >= self._interval_hours * 3600:
                    triggered = True
                    reason = "interval"
                    last_interval_check = time.monotonic()

            if not triggered and self._size_threshold is not None:
                count = self._writer.db.collection.count()
                if count >= self._size_threshold:
                    triggered = True
                    reason = "size_threshold"

            if triggered:
                self._run_cycle(reason)

            self._stop_event.wait(timeout=1.0)

    def _run_cycle(self, reason: str) -> dict:
        memories_before = self._writer.db.collection.count()
        self._save_snapshot()

        deleted = 0
        merged = 0
        summarized = 0

        # Stage 1: deletion
        try:
            result = self._writer.compress_delete(dry_run=self._dry_run)
            deleted = len(result.deleted)
        except Exception:
            logger.exception("Deletion stage failed")

        # Stage 2: merging
        try:
            result = self._writer.compress_merge(dry_run=self._dry_run)
            merged = sum(len(g.members) for g in result.merge_groups)
        except Exception:
            logger.exception("Merging stage failed")

        # Stage 3: summarization
        try:
            result = self._writer.compress_summarize(dry_run=self._dry_run)
            summarized = sum(len(g.members) for g in result.summary_groups)
        except Exception:
            logger.exception("Summarization stage failed")

        memories_after = self._writer.db.collection.count()

        run_result = {
            "trigger": reason,
            "memories_before": memories_before,
            "memories_after": memories_after,
            "deleted": deleted,
            "merged": merged,
            "summarized": summarized,
            "dry_run": self._dry_run,
        }

        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._last_run_time = now
            self._last_run_result = run_result

        self._log.append(run_result)
        return run_result

    def _save_snapshot(self):
        self._snapshots_dir.mkdir(parents=True, exist_ok=True)
        all_memories = self._writer.db.get_all()
        memory_ids = [m.id for m in all_memories]
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        snapshot_path = self._snapshots_dir / f"{stamp}.json"
        with open(snapshot_path, "w") as f:
            json.dump({"timestamp": stamp, "memory_ids": memory_ids}, f)
        self._prune_snapshots()

    def _prune_snapshots(self, keep: int = 5):
        snapshots = sorted(self._snapshots_dir.glob("*.json"))
        for old in snapshots[:-keep]:
            old.unlink()

    def _list_snapshots(self) -> list[str]:
        if not self._snapshots_dir.exists():
            return []
        return sorted(p.stem for p in self._snapshots_dir.glob("*.json"))
