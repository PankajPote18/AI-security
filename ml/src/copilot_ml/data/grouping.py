"""The unit that must never straddle two splits: the "site".

A site is the registered domain, with hosting-platform suffixes (web.app, firebaseapp.com,
weeblysite.com, ...) treated as public suffixes so each tenant is its own site. Without this a
single platform would form one giant group of thousands of unrelated URLs. Hosts with no
registered domain (raw IPs, bare suffixes) fall back to the hostname itself.

The bundled public-suffix snapshot is used: no network access at runtime.
"""

from __future__ import annotations

from urllib.parse import urlsplit

import pandas as pd

from copilot_ml.hostnames import extractor


def site_key(url: str) -> str:
    host = urlsplit(url).hostname
    if not host:
        return url
    return extractor(host).top_domain_under_public_suffix or host


def add_site_column(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = frame.copy()
    grouped["site"] = [site_key(url) for url in grouped["url"]]
    return grouped
