"""Assemble the preprocessing + model `sklearn.Pipeline` that gets fit, evaluated and exported.

Both the preprocessor and the model are inside one `Pipeline`, so the object that is joblib-
dumped at export time is the *entire* transformation from raw feature dict to prediction. There
is no separate preprocessing step inference has to remember to apply.
"""

from __future__ import annotations

from sklearn.base import BaseEstimator
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from copilot_ml.features.schema import CATEGORICAL_FEATURES, FeatureView, feature_names
from copilot_ml.features.tld_encoder import TldFrequencyEncoder


def build_preprocessor(view: FeatureView) -> ColumnTransformer:
    names = feature_names(view)
    categorical = [n for n in names if n in CATEGORICAL_FEATURES]
    numeric = [n for n in names if n not in CATEGORICAL_FEATURES]

    transformers: list[tuple[str, object, list[str]]] = [("numeric", StandardScaler(), numeric)]
    transformers += [(f"{col}_freq", TldFrequencyEncoder(), [col]) for col in categorical]
    return ColumnTransformer(transformers, verbose_feature_names_out=False)


def build_pipeline(estimator: BaseEstimator, view: FeatureView) -> Pipeline:
    return Pipeline([("features", build_preprocessor(view)), ("model", estimator)])
