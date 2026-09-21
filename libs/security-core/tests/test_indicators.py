from security_core.indicators import evaluate_indicators


def _codes(url: str) -> set[str]:
    return {i.code for i in evaluate_indicators(url)}


def test_clean_https_url_triggers_nothing() -> None:
    assert _codes("https://www.example.com/") == set()


def test_plain_http_triggers_not_https() -> None:
    assert "not_https" in _codes("http://example.com/")


def test_raw_ip_host_triggers_ip_host() -> None:
    assert "ip_host" in _codes("http://185.220.1.7/login.php")


def test_userinfo_trick_triggers_userinfo_in_url() -> None:
    assert "userinfo_in_url" in _codes("https://user:pass@evil.com/")


def test_punycode_host_triggers_punycode_host() -> None:
    assert "punycode_host" in _codes("https://xn--80ak6aa92e.com/")


def test_known_shortener_triggers_url_shortener() -> None:
    assert "url_shortener" in _codes("https://bit.ly/abc123")


def test_credential_keyword_in_host_triggers() -> None:
    assert "credential_keyword_in_host" in _codes("https://secure-login.example.net/")


def test_high_entropy_host_triggers() -> None:
    assert "high_entropy_host" in _codes("https://x93kf82jdq7z1m.example.com/")


def test_every_indicator_has_a_title_description_and_severity() -> None:
    url = "http://user:pass@185.220.1.7/verify-account"
    indicators = evaluate_indicators(url)
    assert len(indicators) >= 3
    for indicator in indicators:
        assert indicator.title
        assert indicator.description
        assert indicator.severity in {"info", "low", "medium", "high"}


def test_does_not_raise_on_malformed_url() -> None:
    result = evaluate_indicators("http://[::1")
    assert isinstance(result, list)
