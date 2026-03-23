"""Tests for PineconeDB integration using mocked Pinecone client."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from gilial.core.schema import Memory
from gilial.integrations.pinecone_db import PineconeDB


@pytest.fixture
def sample_memory():
    return Memory.create(
        content="Hello, world!",
        embedding=[0.1] * 1536,
        tags=["greeting"],
        importance_score=0.5,
    )


@pytest.fixture
def mock_pinecone_db():
    with patch("gilial.integrations.pinecone_db.Pinecone") as MockPinecone:
        mock_pc = MockPinecone.return_value
        mock_pc.list_indexes.return_value = []
        mock_index = MagicMock()
        mock_pc.Index.return_value = mock_index
        mock_pc.create_index = MagicMock()

        db = PineconeDB(api_key="fake-key", index_name="test", dimension=1536)
        yield db, mock_index


class TestPineconeAddMemory:
    def test_add_memory(self, mock_pinecone_db, sample_memory):
        db, mock_index = mock_pinecone_db
        db.add_memory(sample_memory)
        mock_index.upsert.assert_called_once()
        call_args = mock_index.upsert.call_args
        vectors = call_args[1]["vectors"] if "vectors" in call_args[1] else call_args[0][0]
        assert vectors[0]["id"] == sample_memory.id
        assert vectors[0]["metadata"]["content"] == "Hello, world!"


class TestPineconeGetById:
    def test_get_by_id_found(self, mock_pinecone_db, sample_memory):
        db, mock_index = mock_pinecone_db
        mock_vec = MagicMock()
        mock_vec.id = sample_memory.id
        mock_vec.values = sample_memory.embedding
        mock_vec.metadata = {
            "content": sample_memory.content,
            "timestamp": sample_memory.timestamp.isoformat(),
            "access_count": 0,
            "importance_score": 0.5,
            "tags": "greeting",
        }
        mock_index.fetch.return_value = MagicMock(vectors={sample_memory.id: mock_vec})

        result = db.get_by_id(sample_memory.id)
        assert result is not None
        assert result.id == sample_memory.id
        assert result.content == "Hello, world!"
        assert "greeting" in result.tags

    def test_get_by_id_not_found(self, mock_pinecone_db):
        db, mock_index = mock_pinecone_db
        mock_index.fetch.return_value = MagicMock(vectors={})
        result = db.get_by_id("nonexistent")
        assert result is None


class TestPineconeUpdateMetadata:
    def test_update_metadata(self, mock_pinecone_db, sample_memory):
        db, mock_index = mock_pinecone_db
        sample_memory.access_count = 5
        db.update_metadata(sample_memory)
        mock_index.update.assert_called_once()
        call_args = mock_index.update.call_args
        assert call_args[1]["set_metadata"]["access_count"] == 5


class TestPineconeGetAll:
    def test_get_all(self, mock_pinecone_db, sample_memory):
        db, mock_index = mock_pinecone_db
        mock_vec = MagicMock()
        mock_vec.id = sample_memory.id
        mock_vec.values = sample_memory.embedding
        mock_vec.metadata = {
            "content": sample_memory.content,
            "timestamp": sample_memory.timestamp.isoformat(),
            "access_count": 0,
            "importance_score": 0.5,
            "tags": "greeting",
        }
        mock_index.list.return_value = [[sample_memory.id]]
        mock_index.fetch.return_value = MagicMock(vectors={sample_memory.id: mock_vec})

        results = db.get_all()
        assert len(results) == 1
        assert results[0].id == sample_memory.id


class TestPineconeDelete:
    def test_delete(self, mock_pinecone_db, sample_memory):
        db, mock_index = mock_pinecone_db
        db.delete(sample_memory.id)
        mock_index.delete.assert_called_once_with(ids=[sample_memory.id])


class TestPineconeSearch:
    def test_search(self, mock_pinecone_db, sample_memory):
        db, mock_index = mock_pinecone_db
        mock_match = MagicMock()
        mock_match.id = sample_memory.id
        mock_match.values = sample_memory.embedding
        mock_match.score = 0.95
        mock_match.metadata = {
            "content": sample_memory.content,
            "timestamp": sample_memory.timestamp.isoformat(),
            "access_count": 0,
            "importance_score": 0.5,
            "tags": "greeting",
        }
        mock_index.query.return_value = MagicMock(matches=[mock_match])

        results = db.search(query_embedding=[0.1] * 1536, n_results=5)
        assert len(results) == 1
        mem, score = results[0]
        assert mem.id == sample_memory.id
        assert mem.content == "Hello, world!"
        assert score == 0.95
