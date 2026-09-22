"""Runs the labelled query set (`queries.yaml`) against a freshly-ingested, in-memory copy of
`knowledge-base/` and computes retrieval metrics. Used both as a standalone report and by the
pytest regression test in this same directory.

    uv run python evals/rag/runner.py
"""

from __future__ import annotations

from pathlib import Path

import yaml
from qdrant_client import QdrantClient

from metrics import EvalSummary, QueryResult, summarize
from rag_core.ingest import ingest_directory
from rag_core.vector_store import DEFAULT_COLLECTION, hybrid_search

QUERIES_PATH = Path(__file__).parent / "queries.yaml"
KB_DIR = Path(__file__).parents[2] / "knowledge-base"
TOP_K = 5


def load_queries(path: Path = QUERIES_PATH) -> list[dict[str, object]]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def run_eval(
    client: QdrantClient,
    kb_dir: Path = KB_DIR,
    queries_path: Path = QUERIES_PATH,
    top_k: int = TOP_K,
) -> tuple[EvalSummary, list[QueryResult]]:
    ingest_directory(client, kb_dir)
    queries = load_queries(queries_path)

    results = []
    for item in queries:
        retrieved = hybrid_search(
            client, str(item["query"]), top_k=top_k, collection_name=DEFAULT_COLLECTION
        )
        retrieved_doc_ids = [str(r.metadata.get("doc_id")) for r in retrieved]
        results.append(
            QueryResult(
                query=str(item["query"]),
                expected_doc_ids=list(item["expected_doc_ids"]),  # type: ignore[arg-type]
                retrieved_doc_ids=retrieved_doc_ids,
            )
        )

    return summarize(results), results


if __name__ == "__main__":
    memory_client = QdrantClient(":memory:")
    summary, results = run_eval(memory_client)
    print(
        f"n={summary.n_queries} hit@1={summary.hit_at_1:.2%} hit@3={summary.hit_at_3:.2%} "
        f"hit@5={summary.hit_at_5:.2%} mrr={summary.mrr:.3f}"
    )
    for r in results:
        if r.rank_of_first_hit is None or r.rank_of_first_hit > 3:
            print(
                f"  weak: {r.query!r} expected={r.expected_doc_ids} got={r.retrieved_doc_ids[:3]}"
            )
