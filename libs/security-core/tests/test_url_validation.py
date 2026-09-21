import pytest

from security_core.url_validation import InvalidUrlError, validate_and_normalize


def test_valid_https_url_round_trips() -> None:
    result = validate_and_normalize("https://Example.COM/Path?q=1")
    assert result.scheme == "https"
    assert result.host == "example.com"
    assert result.normalized == "https://example.com/Path?q=1"


@pytest.mark.parametrize("bad", ["", "   ", None, 123])
def test_empty_or_non_string_is_rejected(bad: object) -> None:
    with pytest.raises(InvalidUrlError):
        validate_and_normalize(bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("scheme", ["ftp", "javascript", "file", "data"])
def test_disallowed_schemes_are_rejected(scheme: str) -> None:
    with pytest.raises(InvalidUrlError, match="not allowed"):
        validate_and_normalize(f"{scheme}://example.com/x")


def test_url_with_no_host_is_rejected() -> None:
    with pytest.raises(InvalidUrlError, match="no host"):
        validate_and_normalize("https:///path")


def test_overlong_url_is_rejected() -> None:
    with pytest.raises(InvalidUrlError, match="exceeds"):
        validate_and_normalize("https://example.com/" + "a" * 3000)


def test_internationalized_domain_is_punycode_encoded() -> None:
    result = validate_and_normalize("https://münchen.example/")
    assert result.host.startswith("xn--")
    assert result.normalized.startswith("https://xn--")


def test_userinfo_is_preserved_not_stripped() -> None:
    # Preserved deliberately: security_core.indicators flags this as suspicious rather than
    # url_validation silently dropping evidence of the trick.
    result = validate_and_normalize("https://user:pass@evil.com/")
    assert result.normalized == "https://user:pass@evil.com/"
    assert result.host == "evil.com"


def test_port_is_preserved() -> None:
    result = validate_and_normalize("https://example.com:8443/")
    assert result.normalized == "https://example.com:8443/"


def test_malformed_port_is_rejected() -> None:
    with pytest.raises(InvalidUrlError):
        validate_and_normalize("https://example.com:notaport/")


def test_original_text_is_preserved_verbatim() -> None:
    result = validate_and_normalize("  https://EXAMPLE.com/x  ")
    assert result.original == "  https://EXAMPLE.com/x  "
