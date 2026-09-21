"""Thin adapter around `copilot_ml.inference.Predictor`: the only place the backend touches the
trained model. Prediction (SHAP included) is CPU-bound, so it runs in a worker thread rather
than blocking the event loop.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import get_settings
from copilot_ml.inference.predictor import Predictor


@dataclass(frozen=True)
class MlPredictionResult:
    model_name: str
    feature_schema_version: str
    artifact_sha256: str
    probability: float
    threshold: float
    label: int
    top_contributions: list[tuple[str, float]]
    latency_ms: float


@lru_cache
def _predictor() -> Predictor:
    return Predictor.load(get_settings().ml_model_dir)


def preload() -> None:
    """Called once at app startup so the first real request doesn't pay the load cost."""
    _predictor()


def current_model_info() -> dict[str, object]:
    metadata = _predictor().metadata
    return {
        "model_name": metadata.model_name,
        "feature_view": metadata.feature_view,
        "feature_schema_version": metadata.feature_schema_version,
        "threshold": metadata.threshold,
        "trained_at": metadata.trained_at,
        "artifact_sha256": metadata.artifact_sha256,
        "val_metrics": metadata.val_metrics,
        "test_metrics": metadata.test_metrics,
    }


async def predict_url(url: str) -> MlPredictionResult:
    predictor = _predictor()
    start = time.perf_counter()
    prediction = await asyncio.to_thread(predictor.predict, url)
    latency_ms = (time.perf_counter() - start) * 1000

    return MlPredictionResult(
        model_name=predictor.metadata.model_name,
        feature_schema_version=predictor.metadata.feature_schema_version,
        artifact_sha256=predictor.metadata.artifact_sha256,
        probability=prediction.probability,
        threshold=prediction.threshold,
        label=prediction.label,
        top_contributions=[(c.feature, c.shap_value) for c in prediction.top_contributions],
        latency_ms=latency_ms,
    )
