"""Compare fitted (model, view) pipelines on a common validation split and pick a champion.

Selection rubric, fixed before results are seen: primary = PR-AUC on validation; tie-breaks =
calibration (lower Brier), then latency, then artifact size, then "simpler is better" (source
order in `training.models.MODEL_SPECS`: logistic regression < random forest < XGBoost).

Production must use the `host` feature view: the M1.1 data card's shortcut audit found that
`full`-view features are dominated by an artefact of how this dataset was sourced (every
legitimate URL is a bare homepage), not a real phishing signal. The champion is therefore chosen
only among `host`-view candidates; `full`-view candidates are still evaluated and reported, so
that decision is demonstrated rather than merely asserted.
"""

from __future__ import annotations

import io
import time
from collections.abc import Sequence
from dataclasses import dataclass

import joblib
from numpy.typing import ArrayLike
from sklearn.pipeline import Pipeline

from copilot_ml.evaluation.metrics import ClassificationMetrics, compute_metrics
from copilot_ml.features.schema import FeatureView
from copilot_ml.training.models import MODEL_NAMES

PRODUCTION_VIEW: FeatureView = "host"
REFERENCE_THRESHOLD = 0.5  # candidates are compared at a common threshold; the champion's own
# operating threshold is chosen separately, on validation, in evaluation.threshold


@dataclass(frozen=True)
class CandidateResult:
    model_name: str
    view: FeatureView
    metrics: ClassificationMetrics
    fit_seconds: float
    predict_seconds: float
    artifact_size_bytes: int

    @property
    def rank_key(self) -> tuple[float, float, float, int, int]:
        model_rank = MODEL_NAMES.index(self.model_name)
        return (
            -self.metrics.pr_auc,
            self.metrics.brier,
            self.predict_seconds,
            self.artifact_size_bytes,
            model_rank,
        )


def _artifact_size_bytes(pipeline: Pipeline) -> int:
    buffer = io.BytesIO()
    joblib.dump(pipeline, buffer)
    return buffer.tell()


def evaluate_candidate(
    model_name: str,
    view: FeatureView,
    pipeline: Pipeline,
    x_val: ArrayLike,
    y_val: ArrayLike,
    fit_seconds: float,
) -> CandidateResult:
    start = time.perf_counter()
    proba = pipeline.predict_proba(x_val)[:, 1]
    predict_seconds = time.perf_counter() - start

    return CandidateResult(
        model_name=model_name,
        view=view,
        metrics=compute_metrics(y_val, proba, threshold=REFERENCE_THRESHOLD),
        fit_seconds=fit_seconds,
        predict_seconds=predict_seconds,
        artifact_size_bytes=_artifact_size_bytes(pipeline),
    )


def rank(results: Sequence[CandidateResult]) -> list[CandidateResult]:
    return sorted(results, key=lambda r: r.rank_key)


def select_champion(results: Sequence[CandidateResult]) -> CandidateResult:
    production_candidates = [r for r in results if r.view == PRODUCTION_VIEW]
    if not production_candidates:
        raise ValueError(f"No candidates for the production view {PRODUCTION_VIEW!r}")
    return rank(production_candidates)[0]
