"""Synthetic dataset with the same quirks as the real one, plus the expected cleaning outcome.

Raw polarity mirrors PhiUSIIL (label 1 = legitimate, 0 = phishing). The legitimate class is
bare `https://host` homepages, phishing has paths / http / IP hosts / multi-URL sites, and a
handful of dirty rows exercise every cleaning rule.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

from copilot_ml.data.sources import PHIUSIIL

N_LEGIT_SITES = 150
N_PHISH_URLS = 40 * 4 + 10 + 10  # 40 multi-URL sites + 10 IP hosts + 10 hosting-platform tenants

EXPECTED_ROWS_OUT = N_LEGIT_SITES + N_PHISH_URLS
EXPECTED_DUPLICATES = 5  # 3 exact + 1 whitespace-padded + 1 case-variant
EXPECTED_MISSING = 2
EXPECTED_UNPARSEABLE = 1
EXPECTED_BAD_SCHEME_OR_HOST = 3
EXPECTED_CONFLICTING = 2

_LEGIT, _PHISH = 1, 0  # raw labels as the source file has them


def fixture_rows() -> list[tuple[str | None, int]]:
    rows: list[tuple[str | None, int]] = [
        (f"https://www.legit-site-{i}.com", _LEGIT) for i in range(N_LEGIT_SITES)
    ]
    rows += [
        (f"http://secure.paypa1-{s}.com/signin/{k}", _PHISH) for s in range(40) for k in range(4)
    ]
    rows += [(f"http://185.220.1.{i}/login.php", _PHISH) for i in range(10)]
    rows += [(f"https://acct-verify-{i}.web.app/", _PHISH) for i in range(10)]

    rows += [("https://www.legit-site-0.com", _LEGIT)] * 3  # exact duplicates
    rows += [("  https://www.legit-site-0.com  ", _LEGIT)]  # whitespace-padded duplicate
    rows += [("HTTPS://WWW.LEGIT-SITE-1.COM", _LEGIT)]  # case-variant duplicate
    rows += [("", _LEGIT), (None, _LEGIT)]  # missing
    rows += [("http://[::1", _PHISH)]  # unparseable
    rows += [("ftp://files.example.org/x", _LEGIT), ("javascript:alert(1)", _PHISH)]
    rows += [("example.com/no-scheme", _LEGIT)]  # no scheme / no host
    rows += [
        ("https://conflict.example.net/x", _LEGIT),
        ("https://conflict.example.net/x", _PHISH),
    ]
    return rows


def write_fixture_archive(path: Path) -> None:
    """Write a PhiUSIIL-shaped zip (with an extra content-derived column that must be ignored)."""
    rows = fixture_rows()
    frame = pd.DataFrame(
        {
            "FILENAME": range(len(rows)),
            PHIUSIIL.url_column: [url for url, _ in rows],
            PHIUSIIL.label_column: [raw for _, raw in rows],
            "HasFavicon": 1,
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as bundle:
        bundle.writestr(PHIUSIIL.archive_member, frame.to_csv(index=False))
