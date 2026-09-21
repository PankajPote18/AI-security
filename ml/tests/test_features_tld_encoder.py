import numpy as np
import pandas as pd
import pytest

from copilot_ml.features.tld_encoder import TldFrequencyEncoder


@pytest.fixture
def fitted() -> TldFrequencyEncoder:
    # com: 4/7, net: 2/7, org: 1/7
    train = pd.Series(["com", "com", "com", "com", "net", "net", "org"])
    return TldFrequencyEncoder(top_k=2).fit(train)  # keeps com, net; org folds into "other"


def test_fit_keeps_top_k_and_pools_the_rest_as_other(fitted: TldFrequencyEncoder) -> None:
    assert set(fitted.frequencies_) == {"com", "net"}
    assert fitted.frequencies_["com"] == pytest.approx(4 / 7)
    assert fitted.other_frequency_ == pytest.approx(1 / 7)


def test_transform_maps_known_and_unseen_categories(fitted: TldFrequencyEncoder) -> None:
    out = fitted.transform(pd.Series(["com", "net", "org", "xyz"]))
    assert out.shape == (4, 1)
    np.testing.assert_allclose(
        out.ravel(),
        [4 / 7, 2 / 7, 1 / 7, 1 / 7],  # org and the never-seen xyz both fall into "other"
    )


def test_accepts_a_single_column_dataframe_like_columntransformer_passes(
    fitted: TldFrequencyEncoder,
) -> None:
    out = fitted.transform(pd.DataFrame({"host_tld": ["com", "net"]}))
    np.testing.assert_allclose(out.ravel(), [4 / 7, 2 / 7])


def test_accepts_a_2d_numpy_array(fitted: TldFrequencyEncoder) -> None:
    out = fitted.transform(np.array([["com"], ["net"]], dtype=object))
    np.testing.assert_allclose(out.ravel(), [4 / 7, 2 / 7])


def test_get_feature_names_out() -> None:
    assert list(TldFrequencyEncoder().get_feature_names_out()) == ["host_tld_freq"]
