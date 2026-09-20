from pathlib import Path

import pandas as pd
import pytest

from copilot_ml.config import MLSettings
from copilot_ml.data.cleaning import clean_urls
from copilot_ml.data.sources import PHIUSIIL
from fixture_data import fixture_rows, write_fixture_archive


@pytest.fixture
def raw_frame() -> pd.DataFrame:
    """Loader-shaped frame (label 1 = phishing) including every kind of dirty row."""
    rows = fixture_rows()
    return pd.DataFrame(
        {
            "url": pd.array([url for url, _ in rows], dtype="string"),
            "label": [0 if raw == 1 else 1 for _, raw in rows],  # raw 0 (phishing) -> 1
            "source_row": range(len(rows)),
        }
    )


@pytest.fixture
def clean_frame(raw_frame: pd.DataFrame) -> pd.DataFrame:
    return clean_urls(raw_frame)[0]


@pytest.fixture
def settings(tmp_path: Path) -> MLSettings:
    # ~330 rows cannot be balanced to production tolerances; those are tested on larger frames.
    return MLSettings(home=tmp_path, seed=7, max_share_gap=0.15, max_class_rate_gap=0.15)


@pytest.fixture
def settings_with_archive(settings: MLSettings) -> MLSettings:
    write_fixture_archive(settings.raw_dir / f"{PHIUSIIL.key}.zip")
    return settings
