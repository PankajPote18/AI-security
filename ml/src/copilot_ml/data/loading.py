"""Read the labelled URLs out of a dataset archive.

Output convention used everywhere downstream: columns `url` (str) and `label`
(int, **1 = phishing, 0 = legitimate**) plus `source_row` (position in the source file).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

from copilot_ml.data.sources import DatasetSource


def load_labeled_urls(archive: Path, source: DatasetSource) -> pd.DataFrame:
    with zipfile.ZipFile(archive) as bundle, bundle.open(source.archive_member) as member:
        raw = pd.read_csv(
            member,
            usecols=[source.url_column, source.label_column],
            dtype={source.url_column: "string"},
        )

    labels = raw[source.label_column]
    if labels.isna().any():
        raise ValueError(f"Missing label values in {source.key}")
    unexpected = set(labels.unique()) - {0, 1}
    if unexpected:
        raise ValueError(f"Unexpected label values in {source.key}: {sorted(unexpected)}")

    return pd.DataFrame(
        {
            "url": raw[source.url_column],
            "label": (labels == source.phishing_label).astype("int8"),
            "source_row": range(len(raw)),
        }
    )
