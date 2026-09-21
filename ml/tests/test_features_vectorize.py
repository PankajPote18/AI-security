from copilot_ml.features.schema import ALL_FEATURES, HOST_FEATURES
from copilot_ml.features.vectorize import extract_feature_frame, select_view

_URLS = ["https://example.com/", "http://185.220.1.7/login", "https://bit.ly/x"]


def test_extract_feature_frame_shape_and_columns() -> None:
    frame = extract_feature_frame(_URLS)
    assert len(frame) == len(_URLS)
    assert list(frame.columns) == list(ALL_FEATURES)


def test_select_view_host_returns_only_host_columns() -> None:
    frame = extract_feature_frame(_URLS)
    host_view = select_view(frame, "host")
    assert list(host_view.columns) == list(HOST_FEATURES)
    assert len(host_view) == len(_URLS)


def test_select_view_full_returns_every_column() -> None:
    frame = extract_feature_frame(_URLS)
    assert list(select_view(frame, "full").columns) == list(ALL_FEATURES)
