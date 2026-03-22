import math
import pytest
from unittest.mock import patch, MagicMock
from gilial.core.writer import MemoryWriter


# ---------------------------------------------------------------------------
# Helpers for deterministic embeddings
# ---------------------------------------------------------------------------

EMBED_DIM = 128  # small dimension, enough for Chroma


def _unit_vector(index: int, dim: int = EMBED_DIM) -> list[float]:
    """Return a unit vector with 1.0 at *index* and 0.0 elsewhere."""
    v = [0.0] * dim
    v[index % dim] = 1.0
    return v


def _noisy_unit_vector(index: int, noise: float = 0.05, dim: int = EMBED_DIM) -> list[float]:
    """Unit vector at *index* with small noise added, then re-normalised."""
    v = _unit_vector(index, dim)
    # add a tiny component on the next axis so it's not identical
    v[(index + 1) % dim] = noise
    norm = math.sqrt(sum(x * x for x in v))
    return [x / norm for x in v]


# ---------------------------------------------------------------------------
# Embedding-call tracker: maps content -> embedding
# ---------------------------------------------------------------------------

class EmbeddingDispatcher:
    """Keeps a registry of content -> embedding so the mock OpenAI client
    returns deterministic, per-content vectors."""

    def __init__(self):
        self._map: dict[str, list[float]] = {}
        self._counter = 0

    def register(self, content: str, embedding: list[float]):
        self._map[content] = embedding

    def get(self, text: str) -> list[float]:
        if text in self._map:
            return self._map[text]
        # fallback: auto-assign a unique axis
        vec = _unit_vector(self._counter)
        self._counter += 1
        self._map[text] = vec
        return vec


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def embedding_dispatcher():
    return EmbeddingDispatcher()


@pytest.fixture()
def mock_writer(tmp_path, embedding_dispatcher):
    """A MemoryWriter with mocked SentenceTransformer that returns predictable embeddings.

    The writer stores data in a temporary Chroma directory and writes
    telemetry into *tmp_path*/telemetry.jsonl.
    """
    chroma_dir = str(tmp_path / "chroma_data")
    telemetry_path = str(tmp_path / "telemetry.jsonl")

    with patch("gilial.core.writer._model") as mock_model:
        import numpy as np
        mock_model.encode.side_effect = lambda text: np.array(embedding_dispatcher.get(text))

        writer = MemoryWriter(chroma_path=chroma_dir)
        writer.telemetry.log_path = tmp_path / "telemetry.jsonl"
        yield writer


# ---------------------------------------------------------------------------
# Sample memories for the 3-cluster retrieval quality test
# ---------------------------------------------------------------------------

# Cluster assignments: geography (axes 0-2), programming (axes 3-5), biology (axes 6-8)
_CLUSTER_DATA = [
    # geography
    ("The Nile is the longest river in Africa, flowing through eleven countries.", ["geography"], _noisy_unit_vector(0)),
    ("Mount Everest stands at 8849 metres above sea level in the Himalayas.", ["geography"], _noisy_unit_vector(1)),
    ("Tokyo is the most populous metropolitan area in the world.", ["geography"], _noisy_unit_vector(2)),
    ("The Amazon rainforest spans nine countries in South America.", ["geography"], _noisy_unit_vector(0, noise=0.1)),
    # programming
    ("Python is a dynamically typed language popular for data science.", ["programming"], _noisy_unit_vector(3)),
    ("Rust guarantees memory safety without a garbage collector.", ["programming"], _noisy_unit_vector(4)),
    ("Git is a distributed version control system created by Linus Torvalds.", ["programming"], _noisy_unit_vector(5)),
    # biology
    ("Mitochondria are the powerhouses of the cell.", ["biology"], _noisy_unit_vector(6)),
    ("DNA carries the genetic instructions for all known organisms.", ["biology"], _noisy_unit_vector(7)),
    ("Photosynthesis converts light energy into chemical energy in plants.", ["biology"], _noisy_unit_vector(8)),
]

# Query embeddings aimed at each cluster centre
_CLUSTER_QUERIES = {
    "geography": _noisy_unit_vector(1, noise=0.08),
    "programming": _noisy_unit_vector(4, noise=0.08),
    "biology": _noisy_unit_vector(7, noise=0.08),
}


@pytest.fixture()
def sample_memories():
    """Return (content, tags, embedding) tuples for the 3-cluster test set."""
    return list(_CLUSTER_DATA)


@pytest.fixture()
def cluster_queries():
    """Return {topic: query_embedding} for the 3-cluster test."""
    return dict(_CLUSTER_QUERIES)
