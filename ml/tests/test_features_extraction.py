import math

import pytest

from copilot_ml.features.extraction import extract_features
from copilot_ml.features.schema import ALL_FEATURES, HOST_FEATURES, feature_names


def test_output_keys_exactly_match_the_schema() -> None:
    assert set(extract_features("https://example.com/")) == set(ALL_FEATURES)


def test_host_view_is_a_strict_subset_of_the_full_view() -> None:
    assert set(HOST_FEATURES) < set(ALL_FEATURES)
    assert set(feature_names("host")) == set(HOST_FEATURES)
    assert set(feature_names("full")) == set(ALL_FEATURES)


@pytest.mark.parametrize("bad", ["", None, 123, "   "])
def test_missing_or_non_string_input_is_all_zero(bad: object) -> None:
    features = extract_features(bad)  # type: ignore[arg-type]
    assert features["host_tld"] == ""
    assert all(v == 0.0 for k, v in features.items() if k != "host_tld")


def test_malformed_url_does_not_raise() -> None:
    features = extract_features("http://[::1")
    assert set(features) == set(ALL_FEATURES)


class TestGoldenVectors:
    def test_bare_https_homepage(self) -> None:
        f = extract_features("https://www.example.com/")
        assert f["scheme_is_https"] == 1.0
        assert f["host_is_ip"] == 0.0
        assert f["has_query"] == 0.0
        assert f["path_depth"] == 0.0
        assert f["host_num_dots"] == 2.0
        assert f["host_subdomain_depth"] == 1.0
        assert f["host_tld"] == "com"

    def test_raw_ip_host(self) -> None:
        f = extract_features("http://185.220.1.7/login.php")
        assert f["scheme_is_https"] == 0.0
        assert f["host_is_ip"] == 1.0
        assert f["host_ip_obfuscated"] == 0.0
        assert f["url_keyword_hits"] >= 1.0

    def test_decimal_obfuscated_ip(self) -> None:
        f = extract_features("http://3232235777/wp-admin")
        assert f["host_is_ip"] == 1.0
        assert f["host_ip_obfuscated"] == 1.0

    def test_brand_lookalike_in_subdomain(self) -> None:
        f = extract_features("https://paypal.verify-account.example.net/")
        assert f["host_brand_lookalike"] == 1.0

    def test_brand_as_the_real_domain_is_not_flagged(self) -> None:
        f = extract_features("https://www.paypal.com/signin")
        assert f["host_brand_lookalike"] == 0.0

    def test_punycode_host(self) -> None:
        f = extract_features("https://xn--80ak6aa92e.com/")
        assert f["host_is_punycode"] == 1.0

    def test_known_shortener(self) -> None:
        f = extract_features("https://bit.ly/abc123")
        assert f["host_is_shortener"] == 1.0

    def test_userinfo_at_symbol_trick(self) -> None:
        f = extract_features("https://user:pass@evil.com/")
        assert f["host_has_userinfo"] == 1.0
        assert f["url_has_at_symbol"] == 1.0

    def test_nonstandard_port(self) -> None:
        f = extract_features("https://example.com:8443/")
        assert f["host_has_port"] == 1.0
        assert f["host_port_nonstandard"] == 1.0

    def test_standard_port_is_not_flagged(self) -> None:
        f = extract_features("https://example.com:443/")
        assert f["host_has_port"] == 1.0
        assert f["host_port_nonstandard"] == 0.0

    def test_query_and_fragment(self) -> None:
        f = extract_features("https://example.com/search?q=1&r=2#top")
        assert f["has_query"] == 1.0
        assert f["num_query_params"] == 2.0
        assert f["has_fragment"] == 1.0

    def test_path_traversal_and_double_slash(self) -> None:
        f = extract_features("https://example.com/a/../b//c")
        assert f["path_num_dot_segments"] >= 1.0
        assert f["path_has_double_slash"] == 1.0

    def test_entropy_is_finite_and_nonnegative(self) -> None:
        f = extract_features("https://x93kf82jd.example.com/a8Fk29z")
        assert math.isfinite(f["host_entropy"])
        assert f["host_entropy"] >= 0.0
        assert math.isfinite(f["url_entropy"])
