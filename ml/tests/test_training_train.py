import numpy as np
import pandas as pd
import pytest

from copilot_ml.features.schema import ALL_FEATURES, HOST_FEATURES
from copilot_ml.features.vectorize import select_view
from copilot_ml.training.models import MODEL_NAMES, MODEL_SPECS
from copilot_ml.training.train import prepare_features, train_all, train_one

_TRAIN = pd.DataFrame(
    {
        "url": [
            "https://a-legit-site.com/",
            "https://another-site.org/",
            "https://third-example.net/",
            "http://185.220.1.7/login",
            "https://bit.ly/verify-account",
            "http://paypal.secure-login.example.ru/signin",
        ]
        * 4,
        "label": [0, 0, 0, 1, 1, 1] * 4,
    }
)


def test_train_all_returns_every_model_view_combination() -> None:
    fitted = train_all(_TRAIN, seed=0)
    assert set(fitted) == {(name, view) for name in MODEL_NAMES for view in ("host", "full")}


def test_each_fitted_pipeline_predicts_valid_probabilities_on_the_right_width() -> None:
    features = prepare_features(_TRAIN)
    for spec in MODEL_SPECS:
        for view, expected_width in (("host", len(HOST_FEATURES)), ("full", len(ALL_FEATURES))):
            pipeline = train_one(spec, view, features, _TRAIN["label"], seed=0)
            x = select_view(features, view)

            proba = pipeline.predict_proba(x)
            assert proba.shape == (len(_TRAIN), 2)
            transformed_width = pipeline.named_steps["features"].transform(x).shape[1]
            assert transformed_width == expected_width


def test_training_is_deterministic_for_a_seed() -> None:
    features = prepare_features(_TRAIN)
    x = select_view(features, "host")

    a = train_all(_TRAIN, seed=7, views=("host",))
    b = train_all(_TRAIN, seed=7, views=("host",))
    for key in a:
        np.testing.assert_allclose(
            a[key].predict_proba(x), b[key].predict_proba(x), err_msg=f"seed mismatch for {key}"
        )


def test_different_seeds_can_change_stochastic_models() -> None:
    features = prepare_features(_TRAIN)
    x = select_view(features, "host")
    rf_a = train_all(_TRAIN, seed=1, views=("host",))[("random_forest", "host")]
    rf_b = train_all(_TRAIN, seed=2, views=("host",))[("random_forest", "host")]
    with pytest.raises(AssertionError):
        np.testing.assert_allclose(rf_a.predict_proba(x), rf_b.predict_proba(x))
