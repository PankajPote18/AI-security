"""URL cleaning: normalise, validate, and remove duplicates and contradictions.

The original URL text is preserved (features are computed from what a user would actually
submit). Only the *dedup key* is canonicalised (lower-cased scheme and host).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from urllib.parse import urlsplit, urlunsplit

import pandas as pd

ALLOWED_SCHEMES = frozenset({"http", "https"})


@dataclass(frozen=True)
class CleaningReport:
    rows_in: int
    dropped_missing: int
    dropped_unparseable: int
    dropped_scheme_or_host: int
    dropped_conflicting_labels: int
    dropped_duplicates: int
    rows_out: int

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def _dedup_key(url: str) -> tuple[str | None, str | None]:
    """Return (canonical_key, rejection_reason); exactly one of the two is None."""
    try:
        parts = urlsplit(url)
    except ValueError:
        return None, "unparseable"
    if parts.scheme.lower() not in ALLOWED_SCHEMES or not parts.hostname:
        return None, "scheme_or_host"
    key = urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, parts.fragment)
    )
    return key, None


def clean_urls(frame: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    rows_in = len(frame)
    cleaned = frame.copy()
    cleaned["url"] = cleaned["url"].astype("string").str.strip()

    present = cleaned["url"].notna() & (cleaned["url"] != "")
    dropped_missing = int((~present).sum())
    cleaned = cleaned[present].copy()
    cleaned["url"] = cleaned["url"].astype(str)

    inspected = [_dedup_key(url) for url in cleaned["url"]]
    cleaned["_key"] = [key for key, _ in inspected]
    reasons = pd.Series([reason for _, reason in inspected], index=cleaned.index)
    dropped_unparseable = int((reasons == "unparseable").sum())
    dropped_scheme_or_host = int((reasons == "scheme_or_host").sum())
    cleaned = cleaned[reasons.isna()]

    # The same URL carrying both labels is unusable for supervised learning: drop every copy.
    contradictory = cleaned.groupby("_key")["label"].transform("nunique") > 1
    dropped_conflicting = int(contradictory.sum())
    cleaned = cleaned[~contradictory]

    before_dedup = len(cleaned)
    cleaned = cleaned.drop_duplicates(subset="_key", keep="first")
    dropped_duplicates = before_dedup - len(cleaned)

    cleaned = cleaned.drop(columns="_key").reset_index(drop=True)
    report = CleaningReport(
        rows_in=rows_in,
        dropped_missing=dropped_missing,
        dropped_unparseable=dropped_unparseable,
        dropped_scheme_or_host=dropped_scheme_or_host,
        dropped_conflicting_labels=dropped_conflicting,
        dropped_duplicates=dropped_duplicates,
        rows_out=len(cleaned),
    )
    return cleaned, report
