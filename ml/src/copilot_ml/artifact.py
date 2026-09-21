"""The shared contract for a trained model artifact: filenames, metadata schema and the
checksum helper.

Both `training.export` (writes an artifact) and `inference.predictor` (reads one) import this
module; they never import each other, which is what lets inference ship without the training
code (and its heavier dependencies) at all.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from copilot_ml.features.schema import FeatureView

ARTIFACT_FILENAME = "phishing_url_model.joblib"
METADATA_FILENAME = "metadata.json"
BACKGROUND_FILENAME = "background_sample.parquet"

_HASH_CHUNK_BYTES = 1024 * 1024


@dataclass(frozen=True)
class ArtifactMetadata:
    feature_schema_version: str
    feature_view: FeatureView
    feature_names: list[str]
    model_name: str
    threshold: float
    artifact_sha256: str
    trained_at: str
    dataset_archive_sha256: str
    val_metrics: dict[str, Any]
    test_metrics: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArtifactMetadata:
        return cls(**data)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_HASH_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()
