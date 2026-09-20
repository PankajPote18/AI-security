import pandas as pd

from copilot_ml.data.cleaning import clean_urls
from fixture_data import (
    EXPECTED_BAD_SCHEME_OR_HOST,
    EXPECTED_CONFLICTING,
    EXPECTED_DUPLICATES,
    EXPECTED_MISSING,
    EXPECTED_ROWS_OUT,
    EXPECTED_UNPARSEABLE,
)


def test_cleaning_report_accounts_for_every_dropped_row(raw_frame: pd.DataFrame) -> None:
    cleaned, report = clean_urls(raw_frame)

    assert report.rows_in == len(raw_frame)
    assert report.dropped_missing == EXPECTED_MISSING
    assert report.dropped_unparseable == EXPECTED_UNPARSEABLE
    assert report.dropped_scheme_or_host == EXPECTED_BAD_SCHEME_OR_HOST
    assert report.dropped_conflicting_labels == EXPECTED_CONFLICTING
    assert report.dropped_duplicates == EXPECTED_DUPLICATES
    assert report.rows_out == EXPECTED_ROWS_OUT == len(cleaned)

    dropped = (
        report.dropped_missing
        + report.dropped_unparseable
        + report.dropped_scheme_or_host
        + report.dropped_conflicting_labels
        + report.dropped_duplicates
    )
    assert report.rows_in - dropped == report.rows_out


def test_conflicting_urls_are_removed_entirely(clean_frame: pd.DataFrame) -> None:
    assert not clean_frame["url"].str.contains("conflict.example.net").any()


def test_original_url_text_is_preserved_apart_from_whitespace() -> None:
    frame = pd.DataFrame(
        {"url": pd.array(["  HTTP://Example.COM/Path?Q=1 "], dtype="string"), "label": [1]}
    )
    cleaned, _ = clean_urls(frame)
    assert cleaned["url"].tolist() == ["HTTP://Example.COM/Path?Q=1"]


def test_case_variants_of_scheme_and_host_are_duplicates_but_path_case_is_not() -> None:
    frame = pd.DataFrame(
        {
            "url": pd.array(
                ["https://a.com/Login", "HTTPS://A.COM/Login", "https://a.com/login"],
                dtype="string",
            ),
            "label": [1, 1, 1],
        }
    )
    cleaned, report = clean_urls(frame)
    assert report.dropped_duplicates == 1
    assert cleaned["url"].tolist() == ["https://a.com/Login", "https://a.com/login"]


def test_index_is_reset_and_input_is_not_mutated(raw_frame: pd.DataFrame) -> None:
    before = raw_frame.copy()
    cleaned, _ = clean_urls(raw_frame)
    pd.testing.assert_frame_equal(raw_frame, before)
    assert cleaned.index.tolist() == list(range(len(cleaned)))
