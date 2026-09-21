from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

from copilot_ml.training.models import MODEL_NAMES, MODEL_SPECS

_EXPECTED_CLASSES = {
    "logistic_regression": LogisticRegression,
    "random_forest": RandomForestClassifier,
    "xgboost": XGBClassifier,
}


def test_model_names_are_exactly_the_three_candidates() -> None:
    assert set(MODEL_NAMES) == set(_EXPECTED_CLASSES)


def test_each_spec_builds_the_right_estimator_type_and_is_seeded() -> None:
    for spec in MODEL_SPECS:
        estimator = spec.build(123)
        assert isinstance(estimator, _EXPECTED_CLASSES[spec.name])
        assert estimator.random_state == 123


def test_build_is_a_fresh_estimator_each_call() -> None:
    spec = MODEL_SPECS[0]
    assert spec.build(1) is not spec.build(1)
