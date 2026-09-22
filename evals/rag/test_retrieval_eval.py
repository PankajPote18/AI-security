"""Retrieval-quality regression test: fails CI if a change to chunking, embeddings, or the
knowledge base itself measurably degrades retrieval quality, rather than only checking that
retrieval runs without error.

Baseline on the current knowledge base (45 labelled queries): hit@1=84%, hit@3=98%, hit@5=100%,
MRR=0.91. Thresholds below leave headroom for legitimate small knowledge-base changes while
still catching a real regression (e.g. a chunking change that breaks heading-aware splitting).
"""

from __future__ import annotations

from pathlib import Path

from qdrant_client import QdrantClient

from rag_core.loaders import load_documents
from runner import load_queries, run_eval

MIN_HIT_AT_3 = 0.90
MIN_HIT_AT_5 = 0.95
MIN_MRR = 0.80

KB_DIR = Path(__file__).parents[2] / "knowledge-base"


def test_retrieval_quality_meets_the_baseline() -> None:
    client = QdrantClient(":memory:")
    summary, results = run_eval(client)

    failures = [
        f"{r.query!r}: expected {r.expected_doc_ids}, got {r.retrieved_doc_ids[:3]}"
        for r in results
        if not r.hit_at_k(5)
    ]

    assert summary.hit_at_3 >= MIN_HIT_AT_3, f"hit@3={summary.hit_at_3:.2%}; failures: {failures}"
    assert summary.hit_at_5 >= MIN_HIT_AT_5, f"hit@5={summary.hit_at_5:.2%}; failures: {failures}"
    assert summary.mrr >= MIN_MRR, f"MRR={summary.mrr:.3f}"


def test_every_query_has_at_least_one_valid_expected_doc_id() -> None:
    """Catches a typo'd doc_id in queries.yaml that would silently make a query un-satisfiable."""
    real_doc_ids = {d.doc_id for d in load_documents(KB_DIR)}

    for item in load_queries():
        expected = set(item["expected_doc_ids"])  # type: ignore[arg-type]
        unknown = expected - real_doc_ids
        assert not unknown, f"{item['query']!r} references unknown doc_id(s): {unknown}"
