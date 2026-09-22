"""Qdrant wrapper: local on-disk mode by default (`QDRANT_PATH`), or a real server if
`QDRANT_URL` is set - both through the same `QdrantClient` API and the same collection schema,
so the choice between them is one environment variable, never a code change.

Local mode allows only one process on a given storage path at a time; the backend and the
(Stage 4) MCP server share the index by running the native Qdrant server and setting `QDRANT_URL`
instead. Hybrid search (dense + sparse, fused with RRF) works identically in both modes.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient, models

from rag_core.embeddings import DENSE_VECTOR_SIZE, embed_dense, embed_sparse

DEFAULT_COLLECTION = "cybersecurity_knowledge"
DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"
DEFAULT_LOCAL_PATH = ".qdrant"
_OVERFETCH_FACTOR = 4  # each prefetch branch pulls this many candidates before RRF fusion


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    metadata: dict[str, Any]


def open_client(path: str | Path | None = None, url: str | None = None) -> QdrantClient:
    resolved_url = url if url is not None else os.environ.get("QDRANT_URL")
    if resolved_url:
        return QdrantClient(url=resolved_url)
    resolved_path = path if path is not None else os.environ.get("QDRANT_PATH", DEFAULT_LOCAL_PATH)
    return QdrantClient(path=str(resolved_path))


def ensure_collection(client: QdrantClient, collection_name: str = DEFAULT_COLLECTION) -> None:
    if client.collection_exists(collection_name):
        return
    client.create_collection(
        collection_name,
        vectors_config={
            DENSE_VECTOR_NAME: models.VectorParams(
                size=DENSE_VECTOR_SIZE, distance=models.Distance.COSINE
            )
        },
        sparse_vectors_config={
            SPARSE_VECTOR_NAME: models.SparseVectorParams(modifier=models.Modifier.IDF)
        },
    )


def chunk_point_id(chunk_id: str) -> str:
    """Qdrant point ids must be an unsigned int or a UUID; derive a stable UUID from our own
    content-hash-based chunk id so re-ingesting the same chunk overwrites rather than duplicates."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def upsert_chunks(
    client: QdrantClient,
    chunk_ids: list[str],
    texts: list[str],
    metadatas: list[dict[str, Any]],
    collection_name: str = DEFAULT_COLLECTION,
) -> None:
    if not chunk_ids:
        return
    dense_vectors = embed_dense(texts)
    sparse_vectors = embed_sparse(texts)
    points = [
        models.PointStruct(
            id=chunk_point_id(chunk_id),
            vector={
                DENSE_VECTOR_NAME: dense,
                SPARSE_VECTOR_NAME: models.SparseVector(
                    indices=sparse.indices, values=sparse.values
                ),
            },
            payload={"chunk_id": chunk_id, "text": text, **metadata},
        )
        for chunk_id, text, dense, sparse, metadata in zip(
            chunk_ids, texts, dense_vectors, sparse_vectors, metadatas, strict=True
        )
    ]
    client.upsert(collection_name, points=points)


def delete_chunks(
    client: QdrantClient, chunk_ids: list[str], collection_name: str = DEFAULT_COLLECTION
) -> None:
    if not chunk_ids:
        return
    client.delete(collection_name, points_selector=[chunk_point_id(c) for c in chunk_ids])


def hybrid_search(
    client: QdrantClient,
    query: str,
    top_k: int = 5,
    collection_name: str = DEFAULT_COLLECTION,
    query_filter: models.Filter | None = None,
) -> list[RetrievedChunk]:
    dense_query = embed_dense([query])[0]
    sparse_query = embed_sparse([query])[0]
    overfetch = top_k * _OVERFETCH_FACTOR

    result = client.query_points(
        collection_name,
        prefetch=[
            models.Prefetch(
                query=dense_query, using=DENSE_VECTOR_NAME, limit=overfetch, filter=query_filter
            ),
            models.Prefetch(
                query=models.SparseVector(indices=sparse_query.indices, values=sparse_query.values),
                using=SPARSE_VECTOR_NAME,
                limit=overfetch,
                filter=query_filter,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=top_k,
    )
    chunks = []
    for point in result.points:
        payload = point.payload or {}
        chunks.append(
            RetrievedChunk(
                chunk_id=str(payload.get("chunk_id", point.id)),
                text=str(payload.get("text", "")),
                score=point.score,
                metadata={k: v for k, v in payload.items() if k not in ("chunk_id", "text")},
            )
        )
    return chunks
