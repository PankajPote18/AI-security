import pandas as pd
import pytest

from copilot_ml.data.labels import LabelPolarityError, verify_label_polarity


def test_correct_polarity_passes_with_large_ratio(clean_frame: pd.DataFrame) -> None:
    check = verify_label_polarity(clean_frame)
    assert check.marker_rate_phishing > 0.9
    assert check.marker_rate_legitimate == 0.0
    assert check.ratio > 100


def test_inverted_labels_are_rejected(clean_frame: pd.DataFrame) -> None:
    inverted = clean_frame.assign(label=1 - clean_frame["label"])
    with pytest.raises(LabelPolarityError, match="inverted"):
        verify_label_polarity(inverted)


def test_no_markers_anywhere_is_rejected() -> None:
    frame = pd.DataFrame(
        {
            "url": ["https://a.com", "https://b.com", "https://c.com", "https://d.com"],
            "label": [1, 1, 0, 0],
        }
    )
    with pytest.raises(LabelPolarityError):
        verify_label_polarity(frame)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/Login",
        "https://example.com/?next=/account",
        "http://user@evil.com",
        "http://192.168.1.10/index.html",
    ],
)
def test_each_marker_kind_is_detected(url: str) -> None:
    frame = pd.DataFrame(
        {"url": [url] * 10 + ["https://plain.com"] * 10, "label": [1] * 10 + [0] * 10}
    )
    assert verify_label_polarity(frame).marker_rate_phishing == 1.0
