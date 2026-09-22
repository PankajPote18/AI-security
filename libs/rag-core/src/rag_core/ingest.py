"""Idempotent knowledge-base ingestion: load -> clean -> chunk -> embed -> upsert, then delete
any previously-indexed chunk that no longer exists (its document was edited or removed).

Only chunks whose content-hash id is not already indexed are embedded and upserted - a chunk
is a candidate for (re-)embedding precisely when its id is new, which is exactly when its
content differs from what is already indexed (see `chunking.chunk_text`). Re-running this on an
unchanged `knowledge-base/` embeds nothing and deletes nothing; it is cheap enough to call on
every app startup, which is what `app.main`'s lifespan does.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from qdrant_client import QdrantClient

from rag_core.chunking import chunk_text
from rag_core.cleaning import clean_markdown
from rag_core.loaders import load_documents
from rag_core.vector_store import (
    DEFAULT_COLLECTION,
    delete_chunks,
    ensure_collection,
    upsert_chunks,
)

_SCROLL_PAGE_SIZE = 256


@dataclass(frozen=True)
class IngestResult:
    documents: int
    chunks: int  # total chunks across all current documents (indexed already or just embedded)
    embedded_chunks: int  # new or changed chunks actually (re-)embedded this run
    deleted_stale_chunks: int


def _existing_chunk_ids(client: QdrantClient, collection_name: str) -> set[str]:
    ids: set[str] = set()
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name, limit=_SCROLL_PAGE_SIZE, offset=offset, with_payload=["chunk_id"]
        )
        ids.update(p.payload["chunk_id"] for p in points if p.payload and "chunk_id" in p.payload)
        if offset is None:
            break
    return ids


def ingest_directory(
    client: QdrantClient, base_dir: Path, collection_name: str = DEFAULT_COLLECTION
) -> IngestResult:
    ensure_collection(client, collection_name)
    documents = load_documents(base_dir)

    chunk_ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict[str, object]] = []
    for doc in documents:
        cleaned = clean_markdown(doc.content)
        for chunk in chunk_text(doc.doc_id, cleaned):
            chunk_ids.append(chunk.chunk_id)
            texts.append(chunk.text)
            metadatas.append(
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "source_name": doc.source_name,
                    "source_url": doc.source_url,
                    "license": doc.license,
                    "topic": doc.topic,
                    "mitre_techniques": list(doc.mitre_techniques),
                    "heading_path": chunk.heading_path,
                }
            )

    before = _existing_chunk_ids(client, collection_name)
    current_ids = set(chunk_ids)

    # A chunk_id already present is byte-identical content already indexed (see chunking.py's
    # content-hash ids) - only chunks whose id is new need embedding.
    to_embed_ids, to_embed_texts, to_embed_metadatas = [], [], []
    for chunk_id, text, metadata in zip(chunk_ids, texts, metadatas, strict=True):
        if chunk_id not in before:
            to_embed_ids.append(chunk_id)
            to_embed_texts.append(text)
            to_embed_metadatas.append(metadata)
    upsert_chunks(client, to_embed_ids, to_embed_texts, to_embed_metadatas, collection_name)

    stale = list(before - current_ids)
    delete_chunks(client, stale, collection_name)

    return IngestResult(
        documents=len(documents),
        chunks=len(chunk_ids),
        embedded_chunks=len(to_embed_ids),
        deleted_stale_chunks=len(stale),
    )
