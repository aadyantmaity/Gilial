import json
import time
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass

import pytest

from gilial.scheduler import CompressionScheduler, CompressionLog


@dataclass
class _FakeDeletionResult:
    deleted: list
    protected: list
    kept: list
    dry_run: bool


@dataclass
class _FakeMergeGroup:
    members: list


@dataclass
class _FakeMergingResult:
    merge_groups: list
    unchanged: list
    dry_run: bool


@dataclass
class _FakeSummaryGroup:
    members: list


@dataclass
class _FakeSummarizationResult:
    summary_groups: list
    unchanged: list
    dry_run: bool


def _make_mock_writer(tmp_path, mem_count=10):
    writer = MagicMock()
    collection = MagicMock()
    collection.count.return_value = mem_count
    writer.db.collection = collection
    writer.db.get_all.return_value = [MagicMock(id=f"mem-{i}") for i in range(mem_count)]

    writer.compress_delete.return_value = _FakeDeletionResult(
        deleted=[MagicMock()], protected=[], kept=[], dry_run=True
    )
    writer.compress_merge.return_value = _FakeMergingResult(
        merge_groups=[_FakeMergeGroup(members=[MagicMock(), MagicMock()])],
        unchanged=[], dry_run=True,
    )
    writer.compress_summarize.return_value = _FakeSummarizationResult(
        summary_groups=[_FakeSummaryGroup(members=[MagicMock(), MagicMock(), MagicMock()])],
        unchanged=[], dry_run=True,
    )
    return writer


class TestRunNow:
    def test_executes_full_pipeline(self, tmp_path):
        writer = _make_mock_writer(tmp_path)
        scheduler = CompressionScheduler(writer=writer, dry_run=True)
        scheduler._snapshots_dir = tmp_path / "snapshots"
        scheduler._log = CompressionLog(path=tmp_path / "compression_log.jsonl")

        result = scheduler.run_now(reason="manual")

        writer.compress_delete.assert_called_once_with(dry_run=True)
        writer.compress_merge.assert_called_once_with(dry_run=True)
        writer.compress_summarize.assert_called_once_with(dry_run=True)

        assert result["trigger"] == "manual"
        assert result["deleted"] == 1
        assert result["merged"] == 2
        assert result["summarized"] == 3
        assert result["dry_run"] is True

    def test_continues_on_stage_error(self, tmp_path):
        writer = _make_mock_writer(tmp_path)
        writer.compress_delete.side_effect = RuntimeError("boom")
        scheduler = CompressionScheduler(writer=writer, dry_run=True)
        scheduler._snapshots_dir = tmp_path / "snapshots"
        scheduler._log = CompressionLog(path=tmp_path / "compression_log.jsonl")

        result = scheduler.run_now()

        assert result["deleted"] == 0
        writer.compress_merge.assert_called_once()
        writer.compress_summarize.assert_called_once()


class TestSizeThresholdTrigger:
    def test_fires_when_above_threshold(self, tmp_path):
        writer = _make_mock_writer(tmp_path, mem_count=50)
        scheduler = CompressionScheduler(
            writer=writer, size_threshold=50, dry_run=True
        )
        scheduler._snapshots_dir = tmp_path / "snapshots"
        scheduler._log = CompressionLog(path=tmp_path / "compression_log.jsonl")

        scheduler.start()
        time.sleep(2.5)
        scheduler.stop()

        assert writer.compress_delete.call_count >= 1

    def test_does_not_fire_below_threshold(self, tmp_path):
        writer = _make_mock_writer(tmp_path, mem_count=5)
        scheduler = CompressionScheduler(
            writer=writer, size_threshold=50, dry_run=True
        )
        scheduler._snapshots_dir = tmp_path / "snapshots"
        scheduler._log = CompressionLog(path=tmp_path / "compression_log.jsonl")

        scheduler.start()
        time.sleep(2.5)
        scheduler.stop()

        writer.compress_delete.assert_not_called()


class TestStatus:
    def test_returns_correct_fields_before_run(self, tmp_path):
        writer = _make_mock_writer(tmp_path)
        scheduler = CompressionScheduler(writer=writer, dry_run=True)
        scheduler._snapshots_dir = tmp_path / "snapshots"

        st = scheduler.status()
        assert st["is_running"] is False
        assert st["last_run_time"] is None
        assert st["last_run_result"] is None
        assert st["snapshots_available"] == []

    def test_returns_correct_fields_after_run(self, tmp_path):
        writer = _make_mock_writer(tmp_path)
        scheduler = CompressionScheduler(writer=writer, dry_run=True)
        scheduler._snapshots_dir = tmp_path / "snapshots"
        scheduler._log = CompressionLog(path=tmp_path / "compression_log.jsonl")

        scheduler.run_now()
        st = scheduler.status()

        assert st["last_run_time"] is not None
        assert st["last_run_result"]["trigger"] == "manual"
        assert isinstance(st["snapshots_available"], list)
        assert len(st["snapshots_available"]) == 1


class TestSnapshots:
    def test_snapshot_written_on_run(self, tmp_path):
        writer = _make_mock_writer(tmp_path)
        scheduler = CompressionScheduler(writer=writer, dry_run=True)
        scheduler._snapshots_dir = tmp_path / "snapshots"
        scheduler._log = CompressionLog(path=tmp_path / "compression_log.jsonl")

        scheduler.run_now()

        snapshots = list((tmp_path / "snapshots").glob("*.json"))
        assert len(snapshots) == 1

        with open(snapshots[0]) as f:
            data = json.load(f)
        assert "memory_ids" in data
        assert len(data["memory_ids"]) == 10

    def test_old_snapshots_pruned_to_five(self, tmp_path):
        writer = _make_mock_writer(tmp_path)
        scheduler = CompressionScheduler(writer=writer, dry_run=True)
        scheduler._snapshots_dir = tmp_path / "snapshots"
        scheduler._log = CompressionLog(path=tmp_path / "compression_log.jsonl")

        for i in range(8):
            scheduler.run_now()
            time.sleep(1.1)

        snapshots = list((tmp_path / "snapshots").glob("*.json"))
        assert len(snapshots) <= 5


class TestCompressionLog:
    def test_log_written_on_run(self, tmp_path):
        writer = _make_mock_writer(tmp_path)
        log_path = tmp_path / "compression_log.jsonl"
        scheduler = CompressionScheduler(writer=writer, dry_run=True)
        scheduler._snapshots_dir = tmp_path / "snapshots"
        scheduler._log = CompressionLog(path=log_path)

        scheduler.run_now()

        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["trigger"] == "manual"
        assert "timestamp" in entry
        assert entry["dry_run"] is True
