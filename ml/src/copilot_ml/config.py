"""Runtime settings for the ML package.

Environment-driven, contains no secrets. Every path and every reproducibility knob
(seed, split proportions) is defined here so no other module hard-codes them.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

ENV_HOME = "COPILOT_ML_HOME"
ENV_SEED = "COPILOT_ML_SEED"
DEFAULT_SEED = 42

SPLIT_NAMES = ("train", "val", "test")


def _default_home() -> Path:
    # src/copilot_ml/config.py -> parents[2] is the `ml/` directory (editable install).
    return Path(__file__).resolve().parents[2]


def _default_split_folds() -> dict[str, int]:
    # 20 stratified group folds -> 14/3/3 = 70% / 15% / 15%.
    return {"train": 14, "val": 3, "test": 3}


@dataclass(frozen=True)
class MLSettings:
    home: Path = field(default_factory=_default_home)
    seed: int = DEFAULT_SEED
    n_folds: int = 20
    split_folds: Mapping[str, int] = field(default_factory=_default_split_folds)
    # Tolerances that make the build fail instead of writing visibly skewed splits.
    max_share_gap: float = 0.02  # |split share of rows - target share|
    max_class_rate_gap: float = 0.01  # |split phishing rate - overall phishing rate|

    def __post_init__(self) -> None:
        if set(self.split_folds) != set(SPLIT_NAMES):
            raise ValueError(f"split_folds must define exactly {SPLIT_NAMES}")
        if sum(self.split_folds.values()) != self.n_folds:
            raise ValueError("split_folds must sum to n_folds")

    @property
    def raw_dir(self) -> Path:
        return self.home / "datasets" / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.home / "datasets" / "processed"

    @property
    def reports_dir(self) -> Path:
        return self.home / "reports"

    @property
    def checksums_path(self) -> Path:
        return self.home / "datasets" / "checksums.json"

    @classmethod
    def from_env(cls) -> MLSettings:
        home = os.environ.get(ENV_HOME)
        seed = os.environ.get(ENV_SEED)
        return cls(
            home=Path(home).resolve() if home else _default_home(),
            seed=int(seed) if seed else DEFAULT_SEED,
        )
