import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from copilot_ml.explain.shap_explainer import (
    global_importance,
    local_contributions,
    shap_values_for_positive_class,
    transform,
    transformed_feature_names,
)
from copilot_ml.features.vectorize import extract_feature_frame, select_view
from copilot_ml.training.pipeline import build_pipeline

_URLS = [
    "https://a-legit-site.com/",
    "https://another-site.org/",
    "http://185.220.1.7/login",
    "https://bit.ly/verify-account",
] * 6
_LABELS = pd.Series([0, 0, 1, 1] * 6)


def _fitted_pipeline() -> tuple[object, pd.DataFrame]:
    features = select_view(extract_feature_frame(_URLS), "host")
    pipeline = build_pipeline(LogisticRegression(max_iter=200), "host")
    pipeline.fit(features, _LABELS)
    return pipeline, features


def test_shap_values_for_positive_class_handles_every_known_shape() -> None:
    two_d = np.zeros((5, 3))
    three_d = np.zeros((5, 3, 2))
    three_d[:, :, 1] = 7.0
    legacy_list = [np.zeros((5, 3)), np.full((5, 3), 9.0)]

    assert shap_values_for_positive_class(two_d).shape == (5, 3)
    np.testing.assert_array_equal(shap_values_for_positive_class(three_d), np.full((5, 3), 7.0))
    np.testing.assert_array_equal(shap_values_for_positive_class(legacy_list), np.full((5, 3), 9.0))


def test_transformed_feature_names_matches_transform_width() -> None:
    pipeline, features = _fitted_pipeline()
    names = transformed_feature_names(pipeline)
    transformed = transform(pipeline, features)
    assert transformed.shape[1] == len(names)


def test_global_importance_covers_every_feature_and_is_nonnegative() -> None:
    pipeline, features = _fitted_pipeline()
    importance = global_importance(pipeline, features, sample_size=10)
    assert set(importance["feature"]) == set(transformed_feature_names(pipeline))
    assert (importance["mean_abs_shap"] >= 0).all()


def test_local_contributions_returns_top_k_sorted_by_absolute_value() -> None:
    pipeline, features = _fitted_pipeline()
    background = transform(pipeline, features)
    contributions = local_contributions(pipeline, features.iloc[[0]], background, top_k=4)

    assert len(contributions) == 4
    magnitudes = [abs(c.shap_value) for c in contributions]
    assert magnitudes == sorted(magnitudes, reverse=True)
