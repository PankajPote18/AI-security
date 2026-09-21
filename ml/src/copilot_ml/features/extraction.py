"""Turn a URL string into the feature dict defined by `schema.ALL_FEATURES`.

This is the single function used by training, evaluation and inference alike (see the package
docstring). It never raises: any input that cannot be parsed as a URL produces a well-defined
all-"empty" feature vector rather than an exception, because inference must survive arbitrary
user input. That guarantee is enforced by a Hypothesis property test.
"""

from __future__ import annotations

import re
import string
from urllib.parse import SplitResult, urlsplit

from copilot_ml.features import schema
from copilot_ml.features.entropy import shannon_entropy
from copilot_ml.features.ip_host import IpHostKind, classify_ip_host
from copilot_ml.features.lexical import brand_names, count_keyword_hits, shortener_domains
from copilot_ml.hostnames import extractor, public_suffix_extractor

_ALLOWED_URL_CHARS = frozenset(string.ascii_letters + string.digits + "-._~:/?#[]@!$&'()*+,;=%")
_TOKEN_SPLIT = re.compile(r"[^a-zA-Z0-9]+")
_STANDARD_PORTS = {"http": 80, "https": 443}


def _longest_token(text: str) -> int:
    tokens = [t for t in _TOKEN_SPLIT.split(text) if t]
    return max((len(t) for t in tokens), default=0)


def _safe_split(url: str) -> SplitResult | None:
    try:
        return urlsplit(url)
    except ValueError:
        return None


def _safe_host(parts: SplitResult) -> str:
    try:
        return (parts.hostname or "").lower()
    except ValueError:
        return ""


def _safe_port(parts: SplitResult) -> int | str | None:
    """Returns the port, None if absent, or the literal "invalid" if it cannot be parsed."""
    try:
        return parts.port
    except ValueError:
        return "invalid"


def _has_userinfo(parts: SplitResult) -> bool:
    try:
        return parts.username is not None or parts.password is not None
    except ValueError:
        return "@" in parts.netloc


def _empty_features() -> dict[str, float | str]:
    values: dict[str, float | str] = dict.fromkeys(schema.ALL_FEATURES, 0.0)
    values["host_tld"] = ""
    return values


def _host_features(url: str, parts: SplitResult) -> dict[str, float | str]:
    host = _safe_host(parts)
    scheme = parts.scheme.lower()
    port = _safe_port(parts)
    ip_kind = classify_ip_host(host)

    port_present = port is not None
    port_nonstandard = bool(port_present) and (
        port == "invalid" or port != _STANDARD_PORTS.get(scheme)
    )

    site = extractor(host) if host else None
    registered_domain = (site.top_domain_under_public_suffix if site else "") or host
    subdomain = site.subdomain if site else ""
    tld = (public_suffix_extractor(host).suffix if host else "") or ""

    digits = sum(c.isdigit() for c in host)
    return {
        "scheme_is_https": float(scheme == "https"),
        "host_length": float(len(host)),
        "host_num_dots": float(host.count(".")),
        "host_num_hyphens": float(host.count("-")),
        "host_num_digits": float(digits),
        "host_digit_ratio": digits / len(host) if host else 0.0,
        "host_subdomain_depth": float(len(subdomain.split("."))) if subdomain else 0.0,
        "host_is_ip": float(ip_kind != IpHostKind.NONE),
        "host_ip_obfuscated": float(ip_kind == IpHostKind.OBFUSCATED),
        "host_has_userinfo": float(_has_userinfo(parts)),
        "host_has_port": float(port_present),
        "host_port_nonstandard": float(port_nonstandard),
        "host_is_punycode": float(any(label.startswith("xn--") for label in host.split("."))),
        "host_is_shortener": float(registered_domain in shortener_domains()),
        "host_keyword_hits": float(count_keyword_hits(host)),
        "host_brand_lookalike": float(
            any(brand in subdomain.lower() for brand in brand_names()) if subdomain else False
        ),
        "host_entropy": shannon_entropy(host),
        "host_longest_token_len": float(_longest_token(host)),
        "host_registered_domain_length": float(len(registered_domain)),
        "host_tld": tld,
    }


def _full_only_features(url: str, parts: SplitResult) -> dict[str, float]:
    path, query = parts.path, parts.query
    digits = sum(c.isdigit() for c in url)
    segments = [s for s in path.split("/") if s]
    return {
        "url_length": float(len(url)),
        "url_num_special_chars": float(sum(1 for c in url if c not in _ALLOWED_URL_CHARS)),
        "url_digit_ratio": digits / len(url) if url else 0.0,
        "url_has_at_symbol": float("@" in url),
        "path_length": float(len(path)),
        "path_depth": float(len(segments)),
        "path_has_double_slash": float("//" in path),
        "path_num_percent_encoded": float(path.count("%")),
        "path_num_dot_segments": float(path.count("..")),
        "has_query": float(bool(query)),
        "num_query_params": float(len(query.split("&"))) if query else 0.0,
        "has_fragment": float(bool(parts.fragment)),
        "url_keyword_hits": float(count_keyword_hits(url)),
        "url_entropy": shannon_entropy(url),
        "url_longest_token_len": float(_longest_token(url)),
        "url_num_slashes": float(url.count("/")),
    }


def extract_features(url: str) -> dict[str, float | str]:
    """Extract all `schema.ALL_FEATURES` from a URL. Never raises; unparseable input -> zeros."""
    if not isinstance(url, str):
        return _empty_features()
    url = url.strip()  # mirrors data.cleaning's normalisation, so features match what was stored
    if not url:
        return _empty_features()

    parts = _safe_split(url)
    if parts is None:
        return _empty_features()

    features: dict[str, float | str] = {}
    features.update(_host_features(url, parts))
    features.update(_full_only_features(url, parts))
    return features
