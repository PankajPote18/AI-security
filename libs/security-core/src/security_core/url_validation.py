"""URL validation and normalisation: the one gate every submitted URL passes through before
anything else touches it (feature extraction, DNS, RDAP, the LLM).

Deliberately permissive about what makes a URL *suspicious* (that's the classifier's and the
indicators' job) and strict about what makes it *unsafe or unparseable* to process at all.
Rejecting a suspicious-looking URL here would be actively wrong: the product exists to analyse
exactly those URLs.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

import idna

ALLOWED_SCHEMES = frozenset({"http", "https"})
MAX_URL_LENGTH = 2048
MAX_HOST_LENGTH = 253


class InvalidUrlError(ValueError):
    """The submitted text cannot be treated as an analysable URL."""


@dataclass(frozen=True)
class NormalizedUrl:
    original: str
    normalized: str  # scheme + host lowercased, host punycode-encoded; path/query untouched
    scheme: str
    host: str  # lowercased, ASCII (punycode if the input was an internationalised domain)


def _encode_host(host: str) -> str:
    if host.isascii():
        return host.lower()
    try:
        return idna.encode(host, uts46=True).decode("ascii")
    except idna.IDNAError as error:
        raise InvalidUrlError(f"Host is not a valid domain name: {error}") from error


def validate_and_normalize(raw: str) -> NormalizedUrl:
    if not isinstance(raw, str):
        raise InvalidUrlError("URL must be a string")
    text = raw.strip()
    if not text:
        raise InvalidUrlError("URL is empty")
    if len(text) > MAX_URL_LENGTH:
        raise InvalidUrlError(f"URL exceeds {MAX_URL_LENGTH} characters")

    try:
        parts = urlsplit(text)
    except ValueError as error:
        raise InvalidUrlError(f"URL could not be parsed: {error}") from error

    scheme = parts.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise InvalidUrlError(f"Scheme {scheme!r} is not allowed; only http/https are analysed")

    try:
        host = parts.hostname
    except ValueError as error:
        raise InvalidUrlError(f"URL host could not be parsed: {error}") from error
    if not host:
        raise InvalidUrlError("URL has no host")

    host_ascii = _encode_host(host).lower()
    if len(host_ascii) > MAX_HOST_LENGTH:
        raise InvalidUrlError(f"Host exceeds {MAX_HOST_LENGTH} characters")

    netloc = host_ascii
    if parts.username:
        userinfo = parts.username + (f":{parts.password}" if parts.password else "")
        netloc = f"{userinfo}@{netloc}"
    try:
        port = parts.port
    except ValueError as error:
        raise InvalidUrlError(f"URL port could not be parsed: {error}") from error
    if port is not None:
        netloc = f"{netloc}:{port}"

    normalized = urlunsplit((scheme, netloc, parts.path, parts.query, parts.fragment))
    return NormalizedUrl(original=raw, normalized=normalized, scheme=scheme, host=host_ascii)
