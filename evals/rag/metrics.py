"""Retrieval-quality metrics: hit@k and mean reciprocal rank (MRR).

No package `__init__.py` here on purpose: this directory is a small, standalone eval script/data
folder (per the project's `evals/**` layout), not a library other packages import. pytest's
default "prepend" import mode adds this directory to `sys.path` for its own test file, which is
what lets `runner.py`'s bare `from metrics import ...` resolve without installing this as a
workspace package.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QueryResult:
    query: str
    expected_doc_ids: list[str]
    retrieved_doc_ids: list[str]  # ranked best-first

    @property
    def rank_of_first_hit(self) -> int | None:
        """1-based rank of the first retrieved doc in `expected_doc_ids`, or None if absent."""
        for rank, doc_id in enumerate(self.retrieved_doc_ids, start=1):
            if doc_id in self.expected_doc_ids:
                return rank
        return None

    def hit_at_k(self, k: int) -> bool:
        rank = self.rank_of_first_hit
        return rank is not None and rank <= k

    @property
    def reciprocal_rank(self) -> float:
        rank = self.rank_of_first_hit
        return 1.0 / rank if rank else 0.0


@dataclass(frozen=True)
class EvalSummary:
    n_queries: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float


def summarize(results: list[QueryResult]) -> EvalSummary:
    n = len(results)
    if n == 0:
        return EvalSummary(n_queries=0, hit_at_1=0.0, hit_at_3=0.0, hit_at_5=0.0, mrr=0.0)
    return EvalSummary(
        n_queries=n,
        hit_at_1=sum(r.hit_at_k(1) for r in results) / n,
        hit_at_3=sum(r.hit_at_k(3) for r in results) / n,
        hit_at_5=sum(r.hit_at_k(5) for r in results) / n,
        mrr=sum(r.reciprocal_rank for r in results) / n,
    )
