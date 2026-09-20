import pandas as pd
import pytest

from copilot_ml.data.audit import COMPOSITE_NAME, shortcut_audit


def _by_name(frame: pd.DataFrame) -> dict:
    return {indicator.name: indicator for indicator in shortcut_audit(frame)}


def test_source_artefacts_are_flagged_as_class_exclusive(clean_frame: pd.DataFrame) -> None:
    indicators = _by_name(clean_frame)
    # legitimate rows are bare https homepages; phishing rows have http/paths
    assert indicators["uses_http"].rate_legitimate == 0.0
    assert indicators["has_path"].rate_legitimate == 0.0
    assert indicators["has_path"].class_exclusive
    assert indicators[COMPOSITE_NAME].class_exclusive


def test_rule_accuracy_is_measured_against_the_labels(clean_frame: pd.DataFrame) -> None:
    composite = _by_name(clean_frame)[COMPOSITE_NAME]
    # The rule catches every phishing URL except the 10 bare-https hosting-tenant homepages,
    # and never misfires on the legitimate homepages.
    assert composite.rule_accuracy == pytest.approx((len(clean_frame) - 10) / len(clean_frame))
    assert composite.rate_legitimate == 0.0


def test_balanced_data_is_not_flagged() -> None:
    urls = ["https://a.com/x", "https://b.com/y", "https://c.com", "https://d.com"] * 5
    frame = pd.DataFrame({"url": urls, "label": [1, 0, 1, 0] * 5})
    indicators = _by_name(frame)
    assert not indicators["has_path"].class_exclusive
    assert indicators["has_path"].rate_phishing == pytest.approx(0.5)
    assert indicators["has_path"].rate_legitimate == pytest.approx(0.5)


@pytest.mark.parametrize(
    ("url", "indicator"),
    [
        ("http://a.com", "uses_http"),
        ("https://a.com/p", "has_path"),
        ("https://a.com/?q=1", "has_query"),
        ("https://a.com/#frag", COMPOSITE_NAME),
        ("https://u@a.com", "has_at_symbol"),
        ("https://10.0.0.1", "ip_host"),
    ],
)
def test_each_indicator_fires_on_its_trigger(url: str, indicator: str) -> None:
    frame = pd.DataFrame({"url": [url, "https://plain.com"], "label": [1, 0]})
    assert _by_name(frame)[indicator].rate_phishing == 1.0


def test_bare_https_homepage_triggers_nothing() -> None:
    frame = pd.DataFrame({"url": ["https://plain.com/", "https://plain.org"], "label": [1, 0]})
    assert all(ind.rate_phishing == 0.0 for ind in shortcut_audit(frame))
