"""Frequency-encode the categorical `host_tld` feature, fit on train only.

The only *stateful* piece of the feature pipeline: how common `.com` vs `.tk` is depends on the
training data, so it cannot be a pure function like the rest of `features/`. It is an
sklearn-compatible transformer so it becomes one step of the exported training `Pipeline` —
the fitted frequencies travel inside the same joblib artifact used for inference, so training
and serving are guaranteed to agree.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

DEFAULT_TOP_K = 50


def _as_series(x: object) -> pd.Series:
    """`ColumnTransformer` hands a single-column selection through as a 1-column DataFrame or
    2D array rather than a Series; accept either so the transformer also works stand-alone."""
    if isinstance(x, pd.DataFrame):
        return x.iloc[:, 0]
    array = np.asarray(x)
    return pd.Series(array.ravel() if array.ndim == 2 else array)


class TldFrequencyEncoder(BaseEstimator, TransformerMixin):
    """Maps a TLD string to its training-set frequency; anything unseen or outside the top-K
    most frequent TLDs is mapped to the frequency of a single shared "other" bucket."""

    def __init__(self, top_k: int = DEFAULT_TOP_K) -> None:
        self.top_k = top_k

    def fit(self, x: object, y: object = None) -> TldFrequencyEncoder:
        counts = _as_series(x).astype(str).value_counts(normalize=True)
        kept = counts.head(self.top_k)
        self.frequencies_: dict[str, float] = {str(k): float(v) for k, v in kept.items()}
        self.other_frequency_: float = float(counts.iloc[self.top_k :].sum())
        return self

    def transform(self, x: object) -> np.ndarray:
        values = _as_series(x).astype(str)
        encoded = values.map(self.frequencies_).fillna(self.other_frequency_)
        return encoded.to_numpy(dtype=float).reshape(-1, 1)

    def get_feature_names_out(self, input_features: object = None) -> np.ndarray:
        return np.array(["host_tld_freq"])
