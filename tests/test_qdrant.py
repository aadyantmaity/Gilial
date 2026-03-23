"""Tests for QdrantDB integration using mocked Qdrant client."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from gilial.core.schema import Memory
from gilial.integrations.qdrant_db import QdrantDB


@pytest.fixture
def sample_memory():
    return Memory.create(
        content="Hello, world!",
        embedding=[0.1] * 1536,
        tags=["greeting"],
        importance_score=0.5,
    )


@pytest.fixture
def mock_qdrant_db():
    with patch("gilial.integrations.qdrant_db.QdrantClient") as MockClient:
        mock_client = MockClient.return_value
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections

        db = QdrantDB(url="http://localhost:6333", collection_name="test", dimension=1536)
        yield db, mock_client


def _mock_point(memory):
    point = MagicMock()
    point.id = memory.id
    point.vector = memory.embedding
    point.payload = {
        "content": memory.content,
        "timestamp": memory.timestamp.isoformat(),
        "access_count": memory.access_count,
        "importance_score": memory.importance_score,
        "tags": memory.tags,
    }
    return point


class TestQdrantAddMemory:
    def test_add_memory(self, mock_qdrant_db, sample_memory):
        db, mock_client = mock_qdrant_db
        db.add_memory(sample_memory)
        mock_client.upsert.assert_called_once()
        call_args = mock_client.upsert.call_args
        assert call_args[1]["collection_name"] == "test"


class TestQdrantGetById:
    def test_get_by_id_found(self, mock_qdrant_db, sample_memory):
        db, mock_client = mock_qdrant_db
        mock_client.retrieve.return_value = [_mock_point(sample_memory)]

        result = db.get_by_id(sample_memory.id)
        assert result is not None
        assert result.id == sample_memory.id
        assert result.content == "Hello, world!"
        assert "greeting" in result.tags

    def test_get_by_id_not_found(self, mock_qdrant_db):
        db, mock_client = mock_qdrant_db
        mock_client.retrieve.return_value = []
        result = db.get_by_id("nonexistent")
        assert result is None


class TestQdrantUpdateMetadata:
    def test_update_metadata(self, mock_qdrant_db, sample_memory):
        db, mock_client = mock_qdrant_db
        sample_memory.access_count = 5
        db.update_metadata(sample_memory)
        mock_client.set_payload.assert_called_once()
        call_args = mock_client.set_payload.call_args
        assert call_args[1]["payload"]["access_count"] == 5


class TestQdrantGetAll:
    def test_get_all(self, mock_qdrant_db, sample_memory):
        db, mock_client = mock_qdrant_db
        mock_client.scroll.return_value = ([_mock_point(sample_memory)], None)

        results = db.get_all()
        assert len(results) == 1
        assert results[0].id == sample_memory.id


class TestQdrantDelete:
    def test_delete(self, mock_qdrant_db, sample_memory):
        db, mock_client = mock_qdrant_db
        db.delete(sample_memory.id)
        mock_client.delete.assert_called_once()


class TestQdrantSearch:
    def test_search(self, mock_qdrant_db, sample_memory):
        db, mock_client = mock_qdrant_db
        mock_point = _mock_point(sample_memory)
        mock_point.score = 0.95
        mock_result = MagicMock()
        mock_result.points = [mock_point]
        mock_client.query_points.return_value = mock_result

        results = db.search(query_embedding=[0.1] * 1536, n_results=5)
        assert len(results) == 1
        mem, score = results[0]
        assert mem.id == sample_memory.id
        assert mem.content == "Hello, world!"
        assert score == 0.95
