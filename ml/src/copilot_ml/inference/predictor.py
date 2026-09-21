"""`Predictor`: the one production entry point for scoring a URL.

Loading verifies the artifact's SHA-256 against the checksum pinned in its own metadata, so a
corrupted or tampered artifact is rejected before any (unpickling) code from it runs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from copilot_ml.artifact import (
    ARTIFACT_FILENAME,
    BACKGROUND_FILENAME,
    METADATA_FILENAME,
    ArtifactMetadata,
    sha256_of,
)
from copilot_ml.explain.shap_explainer import FeatureContribution, local_contributions, transform
from copilot_ml.features.extraction import extract_features

DEFAULT_TOP_K = 5


class ArtifactIntegrityError(RuntimeError):
    """The artifact on disk does not match the checksum recorded in its own metadata."""


@dataclass(frozen=True)
class Prediction:
    url: str
    probability: float
    label: int
    threshold: float
    top_contributions: list[FeatureContribution]


class Predictor:
    """Construct via `Predictor.load(model_dir)`, not directly."""

    def __init__(
        self, pipeline: Pipeline, metadata: ArtifactMetadata, background: pd.DataFrame
    ) -> None:
        self._pipeline = pipeline
        self.metadata = metadata
        self._background_transformed = transform(pipeline, background[metadata.feature_names])

    @classmethod
    def load(cls, model_dir: Path) -> Predictor:
        metadata = ArtifactMetadata.from_dict(
            json.loads((model_dir / METADATA_FILENAME).read_text("utf-8"))
        )
        artifact_path = model_dir / ARTIFACT_FILENAME
        actual = sha256_of(artifact_path)
        if actual != metadata.artifact_sha256:
            raise ArtifactIntegrityError(
                f"{artifact_path.name}: sha256 {actual} != "
                f"metadata.json's {metadata.artifact_sha256}"
            )
        pipeline = joblib.load(artifact_path)
        background = pd.read_parquet(model_dir / BACKGROUND_FILENAME)
        return cls(pipeline, metadata, background)

    def predict(self, url: str, *, top_k: int = DEFAULT_TOP_K) -> Prediction:
        row = pd.DataFrame([extract_features(url)])[self.metadata.feature_names]
        probability = float(self._pipeline.predict_proba(row)[0, 1])
        contributions = local_contributions(
            self._pipeline, row, self._background_transformed, top_k=top_k
        )
        return Prediction(
            url=url,
            probability=probability,
            label=int(probability >= self.metadata.threshold),
            threshold=self.metadata.threshold,
            top_contributions=contributions,
        )
