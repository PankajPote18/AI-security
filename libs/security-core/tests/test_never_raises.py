"""Both functions are called on arbitrary user-submitted text. `evaluate_indicators` must never
raise at all; `validate_and_normalize` may only ever raise its own `InvalidUrlError`, never a
bare ValueError/TypeError/etc leaking out of urllib or idna.

Regression: `evaluate_indicators("http://[::1")` used to raise ValueError("Invalid IPv6 URL")
straight out of `urlsplit`, uncaught.
"""

import contextlib

from hypothesis import given, settings
from hypothesis import strategies as st

from security_core.indicators import evaluate_indicators
from security_core.url_validation import InvalidUrlError, validate_and_normalize


@given(st.text(max_size=300))
@settings(max_examples=300)
def test_evaluate_indicators_never_raises(candidate: str) -> None:
    assert isinstance(evaluate_indicators(candidate), list)


@given(st.text(max_size=300))
@settings(max_examples=300)
def test_validate_and_normalize_only_raises_invalid_url_error(candidate: str) -> None:
    with contextlib.suppress(InvalidUrlError):  # expected for most arbitrary text
        validate_and_normalize(candidate)


def test_the_known_regression_input_directly() -> None:
    assert evaluate_indicators("http://[::1") == []
