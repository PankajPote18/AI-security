"""High-level retrieval: hybrid search plus assembling retrieved chunks into LLM-ready context
text with citation markers, so callers (the backend's report generation) never touch Qdrant
directly."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient

from rag_core.vector_store import DEFAULT_COLLECTION, RetrievedChunk, hybrid_search

DEFAULT_TOP_K = 5


@dataclass(frozen=True)
class RetrievalResult:
    chunks: list[RetrievedChunk]

    def as_context_text(self) -> str:
        """Numbered, titled blocks the LLM can cite back by number - see `llm/prompts`."""
        return "\n\n".join(
            f"[Source {i + 1}: {c.metadata.get('title', c.chunk_id)}]\n{c.text}"
            for i, c in enumerate(self.chunks)
        )

    def as_sources(self) -> list[dict[str, Any]]:
        return [
            {
                "chunk_id": c.chunk_id,
                "doc_id": c.metadata.get("doc_id"),
                "title": c.metadata.get("title"),
                "source_name": c.metadata.get("source_name"),
                "source_url": c.metadata.get("source_url"),
                "topic": c.metadata.get("topic"),
                "score": c.score,
            }
            for c in self.chunks
        ]


def retrieve(
    client: QdrantClient,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    collection_name: str = DEFAULT_COLLECTION,
) -> RetrievalResult:
    return RetrievalResult(
        chunks=hybrid_search(client, query, top_k=top_k, collection_name=collection_name)
    )
