"""Fit every (model, feature view) combination once, extracting features only once too."""

from __future__ import annotations

import pandas as pd
from sklearn.pipeline import Pipeline

from copilot_ml.features.schema import FeatureView
from copilot_ml.features.vectorize import extract_feature_frame, select_view
from copilot_ml.training.models import MODEL_SPECS, ModelSpec
from copilot_ml.training.pipeline import build_pipeline

DEFAULT_VIEWS: tuple[FeatureView, ...] = ("host", "full")


def prepare_features(frame: pd.DataFrame) -> pd.DataFrame:
    return extract_feature_frame(frame["url"])


def train_one(
    spec: ModelSpec, view: FeatureView, features: pd.DataFrame, labels: pd.Series, seed: int
) -> Pipeline:
    pipeline = build_pipeline(spec.build(seed), view)
    pipeline.fit(select_view(features, view), labels)
    return pipeline


def train_all(
    train_frame: pd.DataFrame, seed: int, views: tuple[FeatureView, ...] = DEFAULT_VIEWS
) -> dict[tuple[str, FeatureView], Pipeline]:
    """Returns {(model_name, view): fitted_pipeline} for every model x view combination."""
    features = prepare_features(train_frame)
    labels = train_frame["label"].astype(int)
    return {
        (spec.name, view): train_one(spec, view, features, labels, seed)
        for spec in MODEL_SPECS
        for view in views
    }
