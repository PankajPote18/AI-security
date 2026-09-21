"""The three candidate model families, with one reasoned default configuration each.

A hyperparameter grid is deliberately *not* swept here: model choice is decided by comparing
these three well-configured defaults on the site-disjoint validation split (itself already a
proper held-out group, per `data.splitting`), which is faster and, for a first honest
comparison, exactly as sound as k-fold CV tuning would be. See `docs/adr` for the reasoning.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sklearn.base import BaseEstimator
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier


@dataclass(frozen=True)
class ModelSpec:
    name: str
    build: Callable[[int], BaseEstimator]


def _logistic_regression(seed: int) -> BaseEstimator:
    # Host-view features are on very different scales (ratios in [0,1] vs. lengths in the tens),
    # so LR needs the StandardScaler that `training.pipeline` adds ahead of it.
    return LogisticRegression(max_iter=2000, random_state=seed)


def _random_forest(seed: int) -> BaseEstimator:
    return RandomForestClassifier(
        n_estimators=300,
        max_depth=16,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=seed,
    )


def _xgboost(seed: int) -> BaseEstimator:
    return XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        n_jobs=-1,
        random_state=seed,
    )


MODEL_SPECS: tuple[ModelSpec, ...] = (
    ModelSpec("logistic_regression", _logistic_regression),
    ModelSpec("random_forest", _random_forest),
    ModelSpec("xgboost", _xgboost),
)

MODEL_NAMES: tuple[str, ...] = tuple(spec.name for spec in MODEL_SPECS)
