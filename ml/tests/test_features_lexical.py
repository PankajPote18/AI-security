from copilot_ml.features.lexical import (
    brand_names,
    count_keyword_hits,
    shortener_domains,
    suspicious_keywords,
)


def test_lists_are_nonempty_lowercase_and_commentfree() -> None:
    for loader in (shortener_domains, suspicious_keywords, brand_names):
        words = loader()
        assert words
        assert all(w == w.lower() and not w.startswith("#") for w in words)


def test_known_entries_are_present() -> None:
    assert "bit.ly" in shortener_domains()
    assert "login" in suspicious_keywords()
    assert "paypal" in brand_names()


def test_count_keyword_hits_is_case_insensitive_and_counts_distinct_hits() -> None:
    assert count_keyword_hits("please LOGIN to verify your ACCOUNT") == 3  # login, verify, account
    assert count_keyword_hits("nothing suspicious here") == 0
    assert count_keyword_hits("", keywords=frozenset({"x"})) == 0
