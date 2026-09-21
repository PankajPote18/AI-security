import pytest

from copilot_ml.features.ip_host import IpHostKind, classify_ip_host


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("", IpHostKind.NONE),
        ("example.com", IpHostKind.NONE),
        ("www.example.co.uk", IpHostKind.NONE),
        ("192.168.1.1", IpHostKind.IPV4),
        ("8.8.8.8", IpHostKind.IPV4),
        ("::1", IpHostKind.IPV6),
        ("2001:db8::1", IpHostKind.IPV6),
        ("3232235777", IpHostKind.OBFUSCATED),  # decimal for 192.168.1.1
        ("0xC0A80101", IpHostKind.OBFUSCATED),  # hex for 192.168.1.1
        ("0xC0.0xA8.0x01.0x01", IpHostKind.OBFUSCATED),  # dotted hex
        ("0300.0250.0001.0001", IpHostKind.OBFUSCATED),  # dotted octal
        ("999.999.999.999", IpHostKind.NONE),  # out-of-range octets, not a real IP
        ("1.2.3.4.5", IpHostKind.NONE),  # wrong arity
        ("localhost", IpHostKind.NONE),
    ],
)
def test_classify_ip_host(host: str, expected: IpHostKind) -> None:
    assert classify_ip_host(host) == expected
