"""Detect a URL host that is an IP address, including common obfuscated encodings.

Phishing kits sometimes replace the hostname with an IP written in decimal, octal or hex form
specifically so it does not *look* like an IP at a glance (e.g. `http://3232235521/`,
`http://0xC0.0x00.0x02.0xEB/`). `ipaddress.ip_address` only recognises the plain dotted-decimal
and colon-hex forms, so the obfuscated forms are detected separately.
"""

from __future__ import annotations

import ipaddress
import re
from enum import StrEnum

_DOTTED_OCTET = r"(?:0[xX][0-9a-fA-F]{1,2}|0[0-7]{1,3}|[0-9]{1,3})"
_DOTTED_HEX_OR_OCTAL = re.compile(rf"^{_DOTTED_OCTET}(?:\.{_DOTTED_OCTET}){{3}}$")
_ALL_DECIMAL = re.compile(r"^[0-9]{1,10}$")
_ALL_HEX = re.compile(r"^0[xX][0-9a-fA-F]{1,8}$")


class IpHostKind(StrEnum):
    NONE = "none"
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    OBFUSCATED = "obfuscated"  # decimal / octal / hex encoding of an IPv4 address


def _is_hex(part: str) -> bool:
    return part[:2].lower() == "0x"


def _is_octal(part: str) -> bool:
    return part.startswith("0") and part != "0" and not _is_hex(part)


def _parse_octet(part: str) -> int:
    base = 16 if _is_hex(part) else (8 if _is_octal(part) else 10)
    return int(part, base)


def _looks_like_plain_ip(host: str) -> IpHostKind | None:
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        return None
    return IpHostKind.IPV4 if addr.version == 4 else IpHostKind.IPV6


def classify_ip_host(host: str) -> IpHostKind:
    """Best-effort classification. False negatives are possible; false positives are not."""
    if not host:
        return IpHostKind.NONE

    plain = _looks_like_plain_ip(host)
    if plain is not None:
        return plain

    if _ALL_DECIMAL.match(host) and int(host) <= 0xFFFFFFFF:
        return IpHostKind.OBFUSCATED
    if _ALL_HEX.match(host) and int(host, 16) <= 0xFFFFFFFF:
        return IpHostKind.OBFUSCATED
    if _DOTTED_HEX_OR_OCTAL.match(host):
        parts = host.split(".")
        try:
            octets = [_parse_octet(part) for part in parts]
        except ValueError:
            return IpHostKind.NONE
        is_obfuscated_part = [_is_hex(part) or _is_octal(part) for part in parts]
        if all(0 <= o <= 255 for o in octets) and any(is_obfuscated_part):
            return IpHostKind.OBFUSCATED

    return IpHostKind.NONE
