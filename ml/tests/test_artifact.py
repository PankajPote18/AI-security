import hashlib
from pathlib import Path

from copilot_ml.artifact import ArtifactMetadata, sha256_of


def _metadata(**overrides: object) -> ArtifactMetadata:
    defaults: dict[str, object] = {
        "feature_schema_version": "v1",
        "feature_view": "host",
        "feature_names": ["host_length"],
        "model_name": "logistic_regression",
        "threshold": 0.5,
        "artifact_sha256": "abc123",
        "trained_at": "2026-01-01T00:00:00Z",
        "dataset_archive_sha256": "def456",
        "val_metrics": {"pr_auc": 0.9},
        "test_metrics": {"pr_auc": 0.88},
    }
    defaults.update(overrides)
    return ArtifactMetadata(**defaults)  # type: ignore[arg-type]


def test_as_dict_and_from_dict_round_trip() -> None:
    metadata = _metadata()
    assert ArtifactMetadata.from_dict(metadata.as_dict()) == metadata


def test_sha256_of_matches_hashlib(tmp_path: Path) -> None:
    path = tmp_path / "f.bin"
    content = b"hello world" * 100_000  # larger than the chunk size, to exercise the read loop
    path.write_bytes(content)
    assert sha256_of(path) == hashlib.sha256(content).hexdigest()


def test_sha256_of_is_deterministic_and_content_sensitive(tmp_path: Path) -> None:
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    a.write_bytes(b"same content")
    b.write_bytes(b"same content")
    c = tmp_path / "c.bin"
    c.write_bytes(b"different")

    assert sha256_of(a) == sha256_of(b)
    assert sha256_of(a) != sha256_of(c)
