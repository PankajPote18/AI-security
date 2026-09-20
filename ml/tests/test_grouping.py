import pandas as pd
import pytest

from copilot_ml.data.grouping import add_site_column, site_key


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.example.com/a/b?c=1", "example.com"),
        ("http://secure.login.paypa1-3.com/x", "paypa1-3.com"),
        ("https://EXAMPLE.co.uk", "example.co.uk"),
        # hosting-platform suffixes: every tenant is its own site
        ("https://tenant-a.web.app/", "tenant-a.web.app"),
        ("https://tenant-b.web.app/", "tenant-b.web.app"),
        # no registered domain: fall back to the hostname
        ("http://185.220.1.7/login.php", "185.220.1.7"),
        ("http://[2001:db8::1]/x", "2001:db8::1"),
        ("https://web.app/", "web.app"),
        ("https://localhost/", "localhost"),
    ],
)
def test_site_key(url: str, expected: str) -> None:
    assert site_key(url) == expected


def test_same_site_different_urls_share_a_key() -> None:
    assert site_key("http://a.evil.com/1") == site_key("https://b.evil.com/2")


def test_add_site_column_does_not_mutate_input() -> None:
    frame = pd.DataFrame({"url": ["https://a.com/x"], "label": [1]})
    result = add_site_column(frame)
    assert "site" not in frame.columns
    assert result["site"].tolist() == ["a.com"]
