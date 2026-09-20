"""Shortcut audit: how much of the task can trivial URL-shape rules solve?

Public phishing datasets often build the legitimate class from a different source than the
phishing class (e.g. bare homepages vs. deep phishing links). A model can then score highly by
learning that source difference. This audit measures, per structural indicator, how differently
the two classes behave, and how accurate the one-line rule "indicator => phishing" already is.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import urlsplit

import pandas as pd

COMPOSITE_NAME = "not_bare_https_homepage"

_EXCLUSIVE_LOW = 0.01  # a class that (almost) never shows the indicator...
_EXCLUSIVE_HIGH = 0.05  # ...while the other class shows it at least this often


@dataclass(frozen=True)
class ShortcutIndicator:
    name: str
    description: str
    rate_phishing: float
    rate_legitimate: float
    rule_accuracy: float  # accuracy of the rule "indicator present => phishing"

    @property
    def class_exclusive(self) -> bool:
        low, high = sorted((self.rate_phishing, self.rate_legitimate))
        return low < _EXCLUSIVE_LOW and high >= _EXCLUSIVE_HIGH


def _is_ip(host: str | None) -> bool:
    if not host:
        return False
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True


def _structure_flags(url: str) -> dict[str, bool]:
    parts = urlsplit(url)
    is_http = parts.scheme.lower() == "http"
    has_path = len(parts.path) > 1
    has_query = bool(parts.query)
    return {
        "uses_http": is_http,
        "has_path": has_path,
        "has_query": has_query,
        "has_at_symbol": "@" in url,
        "ip_host": _is_ip(parts.hostname),
        COMPOSITE_NAME: is_http or has_path or has_query or bool(parts.fragment),
    }


_DESCRIPTIONS = {
    "uses_http": "Scheme is plain http",
    "has_path": "Path longer than '/'",
    "has_query": "Query string present",
    "has_at_symbol": "'@' anywhere in the URL",
    "ip_host": "Host is a raw IP address",
    COMPOSITE_NAME: "Anything other than 'https://host[/]' (http, path, query or fragment)",
}


def shortcut_audit(frame: pd.DataFrame) -> list[ShortcutIndicator]:
    flags = pd.DataFrame([_structure_flags(url) for url in frame["url"]], index=frame.index)
    is_phishing = frame["label"] == 1
    return [
        ShortcutIndicator(
            name=name,
            description=_DESCRIPTIONS[name],
            rate_phishing=float(flags.loc[is_phishing, name].mean()),
            rate_legitimate=float(flags.loc[~is_phishing, name].mean()),
            rule_accuracy=float((flags[name] == is_phishing).mean()),
        )
        for name in _DESCRIPTIONS
    ]
