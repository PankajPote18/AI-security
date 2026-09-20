"""Empirical sanity check that the label column means what we think it means.

Documentation can be wrong, and this dataset uses an inverted convention (1 = legitimate), so we
also check the data: URLs labelled phishing must carry markedly more classic phishing markers
(credential-lure keywords, raw IP hosts, `@` tricks) than URLs labelled legitimate.

The marker list here is intentionally independent of the future feature extractor so this check
cannot be fooled by the same code it is meant to protect. It detects gross inversion only; it is
not a substitute for reading the dataset documentation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

_MARKERS = re.compile(
    r"login|signin|verify|secure|account|update|confirm|banking|webscr|password"
    r"|@|^https?://(?:\d{1,3}\.){3}\d{1,3}(?:[:/]|$)",
    re.IGNORECASE,
)
_MIN_RATIO = 3.0
_LEGIT_RATE_FLOOR = 1e-4  # avoids division by ~zero when legit URLs have no markers at all


class LabelPolarityError(ValueError):
    """The label column appears to be inverted relative to the declared mapping."""


@dataclass(frozen=True)
class PolarityCheck:
    marker_rate_phishing: float
    marker_rate_legitimate: float
    ratio: float


def verify_label_polarity(frame: pd.DataFrame, min_ratio: float = _MIN_RATIO) -> PolarityCheck:
    """`frame` uses the normalised convention (label 1 = phishing)."""
    has_marker = frame["url"].str.contains(_MARKERS)
    rate_phishing = float(has_marker[frame["label"] == 1].mean())
    rate_legit = float(has_marker[frame["label"] == 0].mean())
    ratio = rate_phishing / max(rate_legit, _LEGIT_RATE_FLOOR)

    if rate_phishing <= 0 or ratio < min_ratio:
        raise LabelPolarityError(
            f"Labelled-phishing URLs show marker rate {rate_phishing:.4f} vs "
            f"{rate_legit:.4f} for legitimate (ratio {ratio:.1f} < {min_ratio}). "
            "The label mapping is probably inverted."
        )
    return PolarityCheck(rate_phishing, rate_legit, ratio)
