import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from copilot_ml.features.schema import ALL_FEATURES, HOST_FEATURES
from copilot_ml.features.vectorize import extract_feature_frame
from copilot_ml.training.pipeline import build_pipeline, build_preprocessor

_URLS = [
    "https://a-legit-site.com/",
    "https://another-site.org/",
    "http://185.220.1.7/login",
    "https://bit.ly/x",
] * 5
_LABELS = pd.Series([0, 0, 1, 1] * 5)


def test_host_preprocessor_only_consumes_host_columns() -> None:
    frame = extract_feature_frame(_URLS)
    transformed = build_preprocessor("host").fit_transform(frame)
    assert transformed.shape == (len(_URLS), len(HOST_FEATURES))


def test_full_preprocessor_consumes_every_column() -> None:
    frame = extract_feature_frame(_URLS)
    transformed = build_preprocessor("full").fit_transform(frame)
    assert transformed.shape == (len(_URLS), len(ALL_FEATURES))


def test_pipeline_fits_and_predicts_probabilities() -> None:
    frame = extract_feature_frame(_URLS)
    pipeline = build_pipeline(LogisticRegression(max_iter=200), "host")
    pipeline.fit(frame[list(HOST_FEATURES)], _LABELS)

    proba = pipeline.predict_proba(frame[list(HOST_FEATURES)])
    assert proba.shape == (len(_URLS), 2)
    assert ((proba >= 0) & (proba <= 1)).all()
    np.testing.assert_allclose(proba.sum(axis=1), 1.0)
