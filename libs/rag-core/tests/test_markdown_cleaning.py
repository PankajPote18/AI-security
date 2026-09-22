from rag_core.cleaning import clean_markdown


def test_normalizes_crlf_to_lf() -> None:
    assert clean_markdown("a\r\nb\r\n") == "a\nb\n"


def test_strips_trailing_whitespace_on_each_line() -> None:
    assert clean_markdown("a   \nb\t\n") == "a\nb\n"


def test_collapses_runs_of_blank_lines_to_one() -> None:
    assert clean_markdown("a\n\n\n\n\nb\n") == "a\n\nb\n"


def test_result_always_ends_with_exactly_one_newline() -> None:
    assert clean_markdown("a\n\n\n") == "a\n"
    assert clean_markdown("a") == "a\n"


def test_headers_and_normal_spacing_are_preserved() -> None:
    text = "# Title\n\nSome text.\n\n## Subheading\n\nMore text.\n"
    assert clean_markdown(text) == text
