"""Vectorize many URLs into a feature DataFrame and select a view (host-only vs full)."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from copilot_ml.features.extraction import extract_features
from copilot_ml.features.schema import ALL_FEATURES, FeatureView, feature_names


def extract_feature_frame(urls: Iterable[str]) -> pd.DataFrame:
    rows = [extract_features(url) for url in urls]
    return pd.DataFrame(rows, columns=list(ALL_FEATURES))


def select_view(frame: pd.DataFrame, view: FeatureView) -> pd.DataFrame:
    return frame[list(feature_names(view))]
