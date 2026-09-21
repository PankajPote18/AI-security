"""End-to-end training run: fit every (model, view) candidate on train, evaluate all of them on
validation, pick the champion, choose its operating threshold on validation, then touch test
exactly once for the final, reported numbers.

Calibration note: `evaluation.calibration` is available but deliberately not applied to the
exported pipeline. This dataset is ~43% phishing; fitting a sigmoid/isotonic calibrator on it
would calibrate probabilities *to that prevalence*, not to real-world traffic (well under a few
percent phishing) - it would not fix the gap that matters. `evaluation.prevalence.rebase_precision`
addresses that gap at the decision layer instead. Val's reliability curve is still reported, as a
diagnostic of how distorted the raw probabilities are.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import pandas as pd
from sklearn.pipeline import Pipeline

from copilot_ml.evaluation.calibration import ReliabilityCurve, reliability_curve
from copilot_ml.evaluation.comparison import (
    CandidateResult,
    evaluate_candidate,
    rank,
    select_champion,
)
from copilot_ml.evaluation.metrics import ClassificationMetrics, compute_metrics
from copilot_ml.evaluation.prevalence import PrevalenceAdjustedPrecision, rebase_precision
from copilot_ml.evaluation.threshold import select_threshold_max_f1
from copilot_ml.features.vectorize import extract_feature_frame, select_view
from copilot_ml.training.models import MODEL_SPECS
from copilot_ml.training.train import DEFAULT_VIEWS, prepare_features, train_one


@dataclass(frozen=True)
class ExperimentResult:
    candidates: list[CandidateResult]  # every (model, view) combination, ranked
    champion: CandidateResult
    champion_pipeline: Pipeline
    threshold: float
    val_metrics: ClassificationMetrics
    test_metrics: ClassificationMetrics
    val_prevalence_adjusted: PrevalenceAdjustedPrecision
    test_prevalence_adjusted: PrevalenceAdjustedPrecision
    val_reliability: ReliabilityCurve
    # Champion-view feature frames and probabilities, kept so callers (reporting, export) never
    # need to re-extract features or re-run inference to get numbers already computed here.
    train_features: pd.DataFrame
    val_features: pd.DataFrame
    test_features: pd.DataFrame
    val_proba: pd.Series
    test_proba: pd.Series


def run_experiment(
    train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, seed: int
) -> ExperimentResult:
    train_features = prepare_features(train_df)
    val_features = extract_feature_frame(val_df["url"])
    test_features = extract_feature_frame(test_df["url"])

    train_labels = train_df["label"].astype(int)
    val_labels = val_df["label"].astype(int)
    test_labels = test_df["label"].astype(int)

    candidates: list[CandidateResult] = []
    pipelines: dict[tuple[str, str], Pipeline] = {}
    for spec in MODEL_SPECS:
        for view in DEFAULT_VIEWS:
            start = time.perf_counter()
            pipeline = train_one(spec, view, train_features, train_labels, seed)
            fit_seconds = time.perf_counter() - start

            result = evaluate_candidate(
                spec.name, view, pipeline, select_view(val_features, view), val_labels, fit_seconds
            )
            candidates.append(result)
            pipelines[(spec.name, view)] = pipeline

    champion = select_champion(candidates)
    champion_pipeline = pipelines[(champion.model_name, champion.view)]

    x_val = select_view(val_features, champion.view)
    x_test = select_view(test_features, champion.view)
    val_proba = champion_pipeline.predict_proba(x_val)[:, 1]
    test_proba = champion_pipeline.predict_proba(x_test)[:, 1]  # test touched once, here

    threshold = select_threshold_max_f1(val_labels, val_proba)
    val_metrics = compute_metrics(val_labels, val_proba, threshold)
    test_metrics = compute_metrics(test_labels, test_proba, threshold)

    return ExperimentResult(
        candidates=rank(candidates),
        champion=champion,
        champion_pipeline=champion_pipeline,
        threshold=threshold,
        val_metrics=val_metrics,
        test_metrics=test_metrics,
        val_prevalence_adjusted=rebase_precision(val_metrics),
        test_prevalence_adjusted=rebase_precision(test_metrics),
        val_reliability=reliability_curve(val_labels, val_proba),
        train_features=select_view(train_features, champion.view),
        val_features=x_val,
        test_features=x_test,
        val_proba=pd.Series(val_proba, index=val_df.index),
        test_proba=pd.Series(test_proba, index=test_df.index),
    )
