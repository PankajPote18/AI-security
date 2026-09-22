from qdrant_client import QdrantClient

from rag_core.vector_store import DEFAULT_COLLECTION, delete_chunks, hybrid_search, upsert_chunks

_DOCS = [
    (
        "phishing-1",
        "Phishing is a social engineering attack that impersonates a trusted brand to steal "
        "credentials.",
        {"topic": "phishing", "title": "Phishing"},
    ),
    (
        "dns-1",
        "DNS translates domain names into IP addresses. MX records specify a domain's mail "
        "servers.",
        {"topic": "dns", "title": "DNS"},
    ),
    (
        "mitre-1",
        "MITRE ATT&CK T1566 Phishing covers adversaries sending phishing messages for initial "
        "access.",
        {"topic": "mitre", "title": "MITRE"},
    ),
]


def _seed(client: QdrantClient) -> None:
    upsert_chunks(client, [d[0] for d in _DOCS], [d[1] for d in _DOCS], [d[2] for d in _DOCS])


def test_hybrid_search_returns_the_most_relevant_chunk_first(qdrant_client: QdrantClient) -> None:
    _seed(qdrant_client)
    results = hybrid_search(qdrant_client, "MITRE ATT&CK phishing technique", top_k=3)
    assert results
    assert results[0].chunk_id == "mitre-1"


def test_hybrid_search_respects_top_k(qdrant_client: QdrantClient) -> None:
    _seed(qdrant_client)
    results = hybrid_search(qdrant_client, "phishing", top_k=1)
    assert len(results) == 1


def test_upsert_is_idempotent_by_chunk_id(qdrant_client: QdrantClient) -> None:
    _seed(qdrant_client)
    upsert_chunks(qdrant_client, ["phishing-1"], [_DOCS[0][1]], [_DOCS[0][2]])
    count = qdrant_client.count(DEFAULT_COLLECTION).count
    assert count == len(_DOCS)


def test_delete_chunks_removes_them_from_search_results(qdrant_client: QdrantClient) -> None:
    _seed(qdrant_client)
    delete_chunks(qdrant_client, ["mitre-1"])
    results = hybrid_search(qdrant_client, "MITRE ATT&CK phishing technique", top_k=3)
    assert all(r.chunk_id != "mitre-1" for r in results)


def test_metadata_round_trips_through_search(qdrant_client: QdrantClient) -> None:
    _seed(qdrant_client)
    results = hybrid_search(qdrant_client, "DNS mail server", top_k=1)
    assert results[0].metadata["topic"] == "dns"
    assert results[0].metadata["title"] == "DNS"


def test_empty_upsert_does_not_raise(qdrant_client: QdrantClient) -> None:
    upsert_chunks(qdrant_client, [], [], [])  # no-op, must not error
