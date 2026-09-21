"""Build a SHAP explainer for a fitted (preprocessing + model) pipeline.

`shap_values_for_positive_class` normalises across the shapes different SHAP explainer/model
combinations return for binary classification (some return one array per class, some a single
2D array for the positive class, some a 3D array with the class as the last axis) - this is
normalised once here rather than re-guessed at every call site.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shap
from numpy.typing import ArrayLike, NDArray
from sklearn.pipeline import Pipeline

POSITIVE_CLASS_INDEX = 1
_TREE_MODELS = ("RandomForestClassifier", "XGBClassifier")


def transformed_feature_names(pipeline: Pipeline) -> list[str]:
    return list(pipeline.named_steps["features"].get_feature_names_out())


def transform(pipeline: Pipeline, x: pd.DataFrame) -> np.ndarray:
    return np.asarray(pipeline.named_steps["features"].transform(x))


def build_explainer(pipeline: Pipeline, background: NDArray[np.floating]) -> shap.Explainer:
    model = pipeline.named_steps["model"]
    if type(model).__name__ in _TREE_MODELS:
        return shap.TreeExplainer(model)
    if type(model).__name__ == "LogisticRegression":
        return shap.LinearExplainer(model, background)
    return shap.Explainer(model, background)  # generic fallback


def shap_values_for_positive_class(raw: object) -> NDArray[np.floating]:
    """Normalise a SHAP explainer's output to a plain (n_samples, n_features) array of
    contributions towards the phishing (positive) class."""
    if isinstance(raw, list):  # legacy per-class list API
        return np.asarray(raw[POSITIVE_CLASS_INDEX])
    array = np.asarray(raw)
    if array.ndim == 3:  # (n_samples, n_features, n_classes)
        return array[:, :, POSITIVE_CLASS_INDEX]
    return array  # already (n_samples, n_features) for a single-output model


@dataclass(frozen=True)
class FeatureContribution:
    feature: str
    transformed_value: float
    shap_value: float


def global_importance(pipeline: Pipeline, x: pd.DataFrame, sample_size: int = 2000) -> pd.DataFrame:
    sample = x.sample(n=min(sample_size, len(x)), random_state=0) if len(x) > sample_size else x
    transformed = transform(pipeline, sample)
    explainer = build_explainer(pipeline, transformed)
    values = shap_values_for_positive_class(explainer.shap_values(transformed))

    names = transformed_feature_names(pipeline)
    importance = np.abs(values).mean(axis=0)
    return (
        pd.DataFrame({"feature": names, "mean_abs_shap": importance})
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )


def local_contributions(
    pipeline: Pipeline, x_row: pd.DataFrame, background: ArrayLike, top_k: int = 5
) -> list[FeatureContribution]:
    """`background` should be a representative sample (e.g. from the training split), already
    transformed via `transform(pipeline, sample)`, and is reused across calls by the caller."""
    transformed_row = transform(pipeline, x_row)
    explainer = build_explainer(pipeline, np.asarray(background))
    values = shap_values_for_positive_class(explainer.shap_values(transformed_row))[0]

    names = transformed_feature_names(pipeline)
    row = transformed_row[0]
    order = np.argsort(-np.abs(values))[:top_k]
    return [FeatureContribution(names[i], float(row[i]), float(values[i])) for i in order]
