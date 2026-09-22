from pathlib import Path

from qdrant_client import QdrantClient

from rag_core.ingest import ingest_directory
from rag_core.retriever import retrieve
from rag_core.vector_store import DEFAULT_COLLECTION

_DOC_A = """---
title: Phishing Basics
source_name: Test Source
source_url: https://example.com/phishing
license: CC BY 4.0
topic: phishing
mitre_techniques: [T1566]
---

# Phishing Basics

Phishing impersonates a trusted brand to steal credentials.

## Detection

Look for lookalike domains.
"""

_DOC_B = """---
title: DNS Basics
source_name: Test Source
source_url: https://example.com/dns
license: CC BY 4.0
topic: dns
---

# DNS Basics

DNS translates domain names into IP addresses.
"""


def _write_kb(base: Path, docs: dict[str, str]) -> None:
    for name, content in docs.items():
        path = base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_ingest_indexes_every_document(qdrant_client: QdrantClient, tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    _write_kb(kb, {"phishing.md": _DOC_A, "dns.md": _DOC_B})

    result = ingest_directory(qdrant_client, kb)

    assert result.documents == 2
    assert result.chunks > 0
    assert result.embedded_chunks == result.chunks  # everything is new on first ingest
    assert result.deleted_stale_chunks == 0
    assert qdrant_client.count(DEFAULT_COLLECTION).count == result.chunks


def test_ingested_content_is_retrievable(qdrant_client: QdrantClient, tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    _write_kb(kb, {"phishing.md": _DOC_A, "dns.md": _DOC_B})
    ingest_directory(qdrant_client, kb)

    result = retrieve(qdrant_client, "how to detect phishing lookalike domains", top_k=2)
    assert any(c.metadata.get("topic") == "phishing" for c in result.chunks)
    sources = result.as_sources()
    assert sources[0]["source_url"] == "https://example.com/phishing" or any(
        s["topic"] == "phishing" for s in sources
    )


def test_reingesting_unchanged_directory_embeds_nothing(
    qdrant_client: QdrantClient, tmp_path: Path
) -> None:
    # Regression: this used to re-embed every chunk on every call regardless of whether its
    # content had changed, making a startup-time reingest take ~40s instead of being near-free.
    kb = tmp_path / "kb"
    _write_kb(kb, {"phishing.md": _DOC_A, "dns.md": _DOC_B})
    first = ingest_directory(qdrant_client, kb)
    second = ingest_directory(qdrant_client, kb)

    assert second.chunks == first.chunks
    assert second.embedded_chunks == 0
    assert second.deleted_stale_chunks == 0
    assert qdrant_client.count(DEFAULT_COLLECTION).count == first.chunks


def test_editing_a_document_replaces_its_stale_chunks(
    qdrant_client: QdrantClient, tmp_path: Path
) -> None:
    kb = tmp_path / "kb"
    _write_kb(kb, {"phishing.md": _DOC_A})
    ingest_directory(qdrant_client, kb)

    edited = _DOC_A.replace(
        "Look for lookalike domains.", "Look for lookalike domains and urgency language."
    )
    _write_kb(kb, {"phishing.md": edited})
    result = ingest_directory(qdrant_client, kb)

    assert result.embedded_chunks >= 1
    assert result.deleted_stale_chunks >= 1
    retrieved = retrieve(qdrant_client, "urgency language phishing", top_k=1)
    assert "urgency" in retrieved.chunks[0].text


def test_removing_a_document_deletes_all_its_chunks(
    qdrant_client: QdrantClient, tmp_path: Path
) -> None:
    kb = tmp_path / "kb"
    _write_kb(kb, {"phishing.md": _DOC_A, "dns.md": _DOC_B})
    first = ingest_directory(qdrant_client, kb)

    (kb / "dns.md").unlink()
    second = ingest_directory(qdrant_client, kb)

    assert second.documents == 1
    assert second.deleted_stale_chunks == first.chunks - second.chunks
    remaining = qdrant_client.scroll(DEFAULT_COLLECTION, limit=100, with_payload=["topic"])[0]
    assert all(p.payload["topic"] != "dns" for p in remaining)
