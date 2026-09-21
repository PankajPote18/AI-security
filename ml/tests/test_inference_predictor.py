from pathlib import Path

import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from copilot_ml.artifact import ARTIFACT_FILENAME
from copilot_ml.features.vectorize import extract_feature_frame, select_view
from copilot_ml.inference.predictor import ArtifactIntegrityError, Predictor
from copilot_ml.training.export import export_model, sample_background
from copilot_ml.training.pipeline import build_pipeline

_URLS = [
    "https://a-legit-site.com/",
    "https://another-site.org/",
    "https://third-example.net/",
    "http://185.220.1.7/login",
    "https://bit.ly/verify-account",
    "http://paypal.secure-login.example.ru/signin",
] * 6
_LABELS = pd.Series([0, 0, 0, 1, 1, 1] * 6)


@pytest.fixture
def exported_model_dir(tmp_path: Path) -> Path:
    features = select_view(extract_feature_frame(_URLS), "host")
    pipeline = build_pipeline(LogisticRegression(max_iter=200), "host")
    pipeline.fit(features, _LABELS)
    background = sample_background(features, _LABELS, size=10)

    out_dir = tmp_path / "models"
    export_model(
        pipeline,
        out_dir,
        model_name="logistic_regression",
        view="host",
        threshold=0.5,
        dataset_archive_sha256="deadbeef",
        val_metrics={"pr_auc": 0.9},
        test_metrics={"pr_auc": 0.88},
        background=background,
    )
    return out_dir


def test_predictor_loads_and_predicts(exported_model_dir: Path) -> None:
    predictor = Predictor.load(exported_model_dir)
    prediction = predictor.predict("http://185.220.1.7/login")

    assert 0.0 <= prediction.probability <= 1.0
    assert prediction.label in (0, 1)
    assert prediction.threshold == 0.5
    assert len(prediction.top_contributions) == 5
    assert all(isinstance(c.feature, str) for c in prediction.top_contributions)


def test_predictor_never_raises_on_a_garbage_url(exported_model_dir: Path) -> None:
    predictor = Predictor.load(exported_model_dir)
    for garbage in ("", "not a url at all", "http://[::1", "a" * 5000):
        prediction = predictor.predict(garbage)
        assert 0.0 <= prediction.probability <= 1.0


def test_tampered_artifact_is_rejected(exported_model_dir: Path) -> None:
    artifact_path = exported_model_dir / ARTIFACT_FILENAME
    artifact_path.write_bytes(artifact_path.read_bytes() + b"tampered")
    with pytest.raises(ArtifactIntegrityError):
        Predictor.load(exported_model_dir)


def test_metadata_records_the_feature_contract(exported_model_dir: Path) -> None:
    predictor = Predictor.load(exported_model_dir)
    assert predictor.metadata.model_name == "logistic_regression"
    assert predictor.metadata.feature_view == "host"
    assert predictor.metadata.dataset_archive_sha256 == "deadbeef"
