"""Export the champion pipeline as a versioned, checksummed artifact (training-time only).

Writes three files into `out_dir`: the joblib-dumped pipeline, `metadata.json` describing it
(including the artifact's own SHA-256, verified again at load time), and a small stratified
sample of raw feature rows used as the SHAP background reference at inference time - so serving
never needs access to the training data itself.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

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
from copilot_ml.features.schema import FEATURE_SCHEMA_VERSION, FeatureView, feature_names

DEFAULT_BACKGROUND_SIZE = 200


def sample_background(
    features: pd.DataFrame, labels: pd.Series, size: int = DEFAULT_BACKGROUND_SIZE
) -> pd.DataFrame:
    """A class-stratified sample of raw (untransformed) feature rows for SHAP's background."""
    per_class = max(1, size // 2)
    parts = [
        group.sample(n=min(per_class, len(group)), random_state=0)
        for _, group in features.groupby(labels)
    ]
    return pd.concat(parts, ignore_index=True)


def export_model(
    pipeline: Pipeline,
    out_dir: Path,
    *,
    model_name: str,
    view: FeatureView,
    threshold: float,
    dataset_archive_sha256: str,
    val_metrics: dict[str, Any],
    test_metrics: dict[str, Any],
    background: pd.DataFrame,
) -> ArtifactMetadata:
    out_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = out_dir / ARTIFACT_FILENAME
    joblib.dump(pipeline, artifact_path)
    background[list(feature_names(view))].to_parquet(out_dir / BACKGROUND_FILENAME, index=False)

    metadata = ArtifactMetadata(
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        feature_view=view,
        feature_names=list(feature_names(view)),
        model_name=model_name,
        threshold=threshold,
        artifact_sha256=sha256_of(artifact_path),
        trained_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        dataset_archive_sha256=dataset_archive_sha256,
        val_metrics=val_metrics,
        test_metrics=test_metrics,
    )
    metadata_text = json.dumps(metadata.as_dict(), indent=2, sort_keys=True) + "\n"
    (out_dir / METADATA_FILENAME).write_text(metadata_text, encoding="utf-8")
    return metadata
