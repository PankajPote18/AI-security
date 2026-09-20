import pytest
from typer.testing import CliRunner

from copilot_ml.cli import app
from copilot_ml.config import MLSettings

runner = CliRunner()


def test_help_lists_the_data_command() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "data" in result.output


def test_data_help_lists_download_and_build() -> None:
    result = runner.invoke(app, ["data", "--help"])
    assert result.exit_code == 0
    assert "download" in result.output
    assert "build" in result.output


def test_data_build_end_to_end(
    monkeypatch: pytest.MonkeyPatch, settings_with_archive: MLSettings
) -> None:
    # The CLI reads settings from the environment; hand it the fixture's small-data tolerances.
    monkeypatch.setattr(MLSettings, "from_env", lambda: settings_with_archive)
    result = runner.invoke(app, ["data", "build"])

    assert result.exit_code == 0, result.output
    assert "train" in result.output
    assert (settings_with_archive.reports_dir / "data_card.md").exists()
