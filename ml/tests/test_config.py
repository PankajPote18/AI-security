from pathlib import Path

import pytest

from copilot_ml.config import DEFAULT_SEED, ENV_HOME, ENV_SEED, MLSettings


def test_defaults_point_at_ml_directory() -> None:
    settings = MLSettings()
    assert settings.home.name == "ml"
    assert settings.seed == DEFAULT_SEED
    assert settings.raw_dir == settings.home / "datasets" / "raw"


def test_from_env_overrides_home_and_seed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(ENV_HOME, str(tmp_path))
    monkeypatch.setenv(ENV_SEED, "123")
    settings = MLSettings.from_env()
    assert settings.home == tmp_path.resolve()
    assert settings.seed == 123


def test_split_folds_must_sum_to_n_folds() -> None:
    with pytest.raises(ValueError, match="sum to n_folds"):
        MLSettings(split_folds={"train": 10, "val": 3, "test": 3})


def test_split_folds_must_name_all_splits() -> None:
    with pytest.raises(ValueError, match="exactly"):
        MLSettings(split_folds={"train": 17, "test": 3})
