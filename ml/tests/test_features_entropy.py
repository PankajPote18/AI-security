import pytest

from copilot_ml.features.entropy import shannon_entropy


def test_empty_string_has_zero_entropy() -> None:
    assert shannon_entropy("") == 0.0


def test_single_repeated_character_has_zero_entropy() -> None:
    assert shannon_entropy("aaaaaa") == 0.0


def test_two_equally_likely_symbols_have_entropy_one() -> None:
    assert shannon_entropy("abababab") == pytest.approx(1.0)


def test_more_distinct_characters_increase_entropy() -> None:
    assert shannon_entropy("aaaabbbb") < shannon_entropy("abcdefgh")
