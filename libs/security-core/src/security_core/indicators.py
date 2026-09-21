"""Rule-based structural security indicators, each mapped to a MITRE ATT&CK technique, for the
evidence bundle's human-readable "Security Indicators" section.

These are presentation-facing signals, separate from the ML model's numeric features
(`copilot_ml.features`) even though they inspect the same URL: the ML features are versioned and
shaped for one trained model's schema; these are shaped for direct display and for
`scoring_service`'s deterministic weighting, and can be reworded or extended independently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import SplitResult, urlsplit

from security_core.entropy import shannon_entropy
from security_core.hostnames import extractor
from security_core.ip_host import IpHostKind, classify_ip_host

Severity = Literal["info", "low", "medium", "high"]

# A small, curated set for direct user-facing explanation - deliberately not shared with
# copilot_ml.features.lexical, which is a larger, versioned list feeding the ML schema (see
# ADR-0001). Diverging wording here is fine; the two serve different consumers.
_SUSPICIOUS_KEYWORDS = frozenset(
    {
        "login",
        "signin",
        "verify",
        "secure",
        "account",
        "update",
        "confirm",
        "banking",
        "webscr",
        "password",
        "wallet",
        "suspend",
        "unlock",
    }
)
_SHORTENER_DOMAINS = frozenset(
    {
        "bit.ly",
        "tinyurl.com",
        "goo.gl",
        "t.co",
        "ow.ly",
        "is.gd",
        "buff.ly",
        "rebrand.ly",
        "cutt.ly",
        "tiny.cc",
        "rb.gy",
        "t.ly",
    }
)
_HIGH_ENTROPY_THRESHOLD = 3.8  # empirically, random-looking hostnames tend to sit above this


@dataclass(frozen=True)
class Indicator:
    code: str
    severity: Severity
    title: str
    description: str
    mitre_technique: str | None  # e.g. "T1583.001" (Acquire Infrastructure: Domains)


def _safe_split(url: str) -> SplitResult | None:
    try:
        parts = urlsplit(url)
        _ = parts.hostname  # forces bracket/host validation now, not lazily at first use below
    except ValueError:
        return None
    return parts


def evaluate_indicators(url: str) -> list[Indicator]:
    """Never raises: unparseable input (e.g. a malformed IPv6 host) simply yields no indicators
    rather than crashing the analysis pipeline that calls this on user-submitted text."""
    parts = _safe_split(url)
    if parts is None:
        return []
    host = (parts.hostname or "").lower()
    found: list[Indicator] = []

    if parts.scheme.lower() != "https":
        found.append(
            Indicator(
                code="not_https",
                severity="medium",
                title="Not served over HTTPS",
                description=(
                    "The URL uses plain HTTP; a page mimicking a login form over an "
                    "unencrypted connection is both easier to intercept and a signal the "
                    "page is not the real site."
                ),
                mitre_technique="T1557",
            )
        )

    ip_kind = classify_ip_host(host)
    if ip_kind != IpHostKind.NONE:
        obfuscated = " (obfuscated encoding)" if ip_kind == IpHostKind.OBFUSCATED else ""
        found.append(
            Indicator(
                code="ip_host",
                severity="high",
                title=f"Host is a raw IP address{obfuscated}",
                description=(
                    "Legitimate sites are almost always referenced by domain name; a raw IP "
                    "address host is a classic sign of throwaway phishing infrastructure."
                ),
                mitre_technique="T1583.001",
            )
        )

    if parts.username or parts.password:
        found.append(
            Indicator(
                code="userinfo_in_url",
                severity="high",
                title="'@' userinfo trick in the URL",
                description=(
                    "Everything before an '@' in a URL's authority is login-credential syntax "
                    "the browser discards; attackers put a trusted-looking domain there to "
                    "disguise the real (attacker-controlled) host that follows the '@'."
                ),
                mitre_technique="T1204.001",
            )
        )

    if any(label.startswith("xn--") for label in host.split(".")):
        found.append(
            Indicator(
                code="punycode_host",
                severity="medium",
                title="Internationalised (punycode) domain",
                description=(
                    "The domain contains non-ASCII characters encoded as punycode, a technique "
                    "used to register look-alike domains with visually similar characters from "
                    "other alphabets."
                ),
                mitre_technique="T1583.001",
            )
        )

    registered_domain = extractor(host).top_domain_under_public_suffix if host else ""
    if registered_domain in _SHORTENER_DOMAINS:
        found.append(
            Indicator(
                code="url_shortener",
                severity="low",
                title="Known URL shortener",
                description=(
                    "URL shorteners hide the real destination until the link is followed; not "
                    "inherently malicious, but commonly used to bypass link scanners."
                ),
                mitre_technique="T1027",
            )
        )

    if any(keyword in host for keyword in _SUSPICIOUS_KEYWORDS):
        found.append(
            Indicator(
                code="credential_keyword_in_host",
                severity="medium",
                title="Credential-related keyword in the domain",
                description=(
                    "The domain itself (not just the page content) contains a login/verify/"
                    "account-style keyword, a common pattern in domains registered specifically "
                    "to impersonate an account or security page."
                ),
                mitre_technique="T1566.002",
            )
        )

    if host and shannon_entropy(host) >= _HIGH_ENTROPY_THRESHOLD:
        found.append(
            Indicator(
                code="high_entropy_host",
                severity="low",
                title="High-entropy (random-looking) domain",
                description=(
                    "The domain looks close to random characters, typical of automatically "
                    "generated or throwaway phishing domains rather than a memorable brand name."
                ),
                mitre_technique="T1568.002",
            )
        )

    return found
