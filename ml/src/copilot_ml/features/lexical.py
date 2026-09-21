"""Versioned word lists (keywords, shorteners, brand names) loaded from `features/data/*.txt`.

Kept as data files rather than literals in code so they can be reviewed, extended and diffed
independently of the extraction logic that uses them.
"""

from __future__ import annotations

from functools import cache
from importlib import resources


@cache
def _load(filename: str) -> frozenset[str]:
    text = resources.files("copilot_ml.features.data").joinpath(filename).read_text("utf-8")
    return frozenset(
        line.strip().lower()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def shortener_domains() -> frozenset[str]:
    return _load("shortener_domains.txt")


def suspicious_keywords() -> frozenset[str]:
    return _load("suspicious_keywords.txt")


def brand_names() -> frozenset[str]:
    return _load("brand_names.txt")


def count_keyword_hits(text: str, keywords: frozenset[str] | None = None) -> int:
    lowered = text.lower()
    return sum(1 for kw in (keywords or suspicious_keywords()) if kw in lowered)
