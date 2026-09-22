"""Dense + sparse embedding models, wrapped behind one interface so `vector_store` never
depends on fastembed's specific API. Both run locally via ONNX (ready after a one-time model
download to the fastembed cache) - no embedding API key or network call at query time.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from fastembed import SparseTextEmbedding, TextEmbedding

DENSE_MODEL_NAME = "BAAI/bge-small-en-v1.5"
DENSE_VECTOR_SIZE = 384
SPARSE_MODEL_NAME = "Qdrant/bm25"


@dataclass(frozen=True)
class SparseVector:
    indices: list[int]
    values: list[float]


@lru_cache
def _dense_model() -> TextEmbedding:
    return TextEmbedding(model_name=DENSE_MODEL_NAME)


@lru_cache
def _sparse_model() -> SparseTextEmbedding:
    return SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)


def embed_dense(texts: list[str]) -> list[list[float]]:
    return [vector.tolist() for vector in _dense_model().embed(texts)]


def embed_sparse(texts: list[str]) -> list[SparseVector]:
    return [
        SparseVector(v.indices.tolist(), v.values.tolist()) for v in _sparse_model().embed(texts)
    ]
