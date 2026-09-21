"""Property test: the extractor must never raise, on any string a user could paste in."""

import math

from hypothesis import given, settings
from hypothesis import strategies as st

from copilot_ml.features.extraction import extract_features
from copilot_ml.features.schema import ALL_FEATURES, CATEGORICAL_FEATURES


@given(st.text(max_size=500))
@settings(max_examples=300)
def test_extract_features_never_raises_and_matches_schema(candidate: str) -> None:
    features = extract_features(candidate)

    assert set(features) == set(ALL_FEATURES)
    for name in ALL_FEATURES:
        value = features[name]
        if name in CATEGORICAL_FEATURES:
            assert isinstance(value, str)
        else:
            assert isinstance(value, float)
            assert math.isfinite(value)
