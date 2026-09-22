"""Real local-mode Qdrant per test (SQLite-backed, no server, no Docker). The embedding models
are cached process-wide (`rag_core.embeddings`'s `lru_cache`), so only the first test in a run
pays the one-time ONNX model download.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from qdrant_client import QdrantClient

from rag_core.vector_store import ensure_collection, open_client


@pytest.fixture
def qdrant_client(tmp_path: Path) -> Iterator[QdrantClient]:
    client = open_client(path=tmp_path / "qdrant")
    ensure_collection(client)
    yield client
    client.close()
