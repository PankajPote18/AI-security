"""Descriptions of the datasets the pipeline knows how to ingest."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetSource:
    key: str
    title: str
    homepage: str
    download_url: str
    archive_member: str
    url_column: str
    label_column: str
    phishing_label: int  # raw value in `label_column` that means "phishing"
    license: str
    citation: str


# Label semantics confirmed on the UCI dataset page: "Label 1 corresponds to a legitimate URL,
# label 0 to a phishing URL" (i.e. inverted vs. the usual 1 = positive/phishing convention).
# Only the URL text and label are used. The source's ~50 precomputed columns are derived from
# page content and are intentionally ignored.
PHIUSIIL = DatasetSource(
    key="phiusiil",
    title="PhiUSIIL Phishing URL Dataset",
    homepage="https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset",
    download_url="https://archive.ics.uci.edu/static/public/967/phiusiil+phishing+url+dataset.zip",
    archive_member="PhiUSIIL_Phishing_URL_Dataset.csv",
    url_column="URL",
    label_column="label",
    phishing_label=0,
    license="CC BY 4.0",
    citation=(
        "Prasad, A. and Chandra, S. (2024). PhiUSIIL Phishing URL Dataset. "
        "UCI Machine Learning Repository."
    ),
)
