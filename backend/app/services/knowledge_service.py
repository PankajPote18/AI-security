"""Thin adapter over `rag_core`: the only place the backend touches Qdrant. One process-wide
client (local on-disk mode by default, or a real server if `QDRANT_URL` is set - see
`rag_core.vector_store.open_client`), opened lazily on first use.
"""

from __future__ import annotations

from functools import lru_cache

from qdrant_client import QdrantClient

from app.core.config import get_settings
from rag_core.ingest import IngestResult, ingest_directory
from rag_core.retriever import RetrievalResult, retrieve


@lru_cache
def _client() -> QdrantClient:
    return QdrantClient(path=str(get_settings().knowledge_base_dir.parent / ".qdrant"))


def search(query: str, top_k: int = 5) -> RetrievalResult:
    return retrieve(_client(), query, top_k=top_k)


def reingest() -> IngestResult:
    """Rebuild the index from `knowledge-base/`. Called at startup and by an admin/debug path -
    never automatically on every request, since ingestion is not free."""
    return ingest_directory(_client(), get_settings().knowledge_base_dir)
