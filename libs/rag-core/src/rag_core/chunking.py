"""Header-aware chunking: split on markdown headers first (so a chunk never straddles two
sections), then recursively split any section still too long. Each chunk gets a content-hash id
that changes if and only if its own text changes, so `ingest`'s upsert is idempotent and a
changed chunk's stale predecessor is detectable (and deletable) rather than left orphaned.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
_HEADER_LEVELS: list[tuple[str, str]] = [("#", "h1"), ("##", "h2"), ("###", "h3")]


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    heading_path: str  # e.g. "Phishing > Common techniques"
    chunk_index: int


def _heading_path(metadata: dict[str, str]) -> str:
    return " > ".join(metadata[key] for _, key in _HEADER_LEVELS if key in metadata)


def chunk_text(doc_id: str, text: str) -> list[Chunk]:
    header_splits = MarkdownHeaderTextSplitter(_HEADER_LEVELS, strip_headers=False).split_text(text)
    pieces = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    ).split_documents(header_splits)

    chunks: list[Chunk] = []
    for index, piece in enumerate(pieces):
        content = piece.page_content.strip()
        if not content:
            continue
        digest = hashlib.sha256(f"{doc_id}:{index}:{content}".encode()).hexdigest()[:16]
        chunks.append(
            Chunk(
                chunk_id=f"{doc_id}#{digest}",
                text=content,
                heading_path=_heading_path(piece.metadata),
                chunk_index=index,
            )
        )
    return chunks
