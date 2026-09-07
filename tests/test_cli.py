from typer.testing import CliRunner

from benchpub.cli import app

runner = CliRunner()


def test_no_arguments_show_help_successfully() -> None:
    result = runner.invoke(app)

    assert result.exit_code == 0
    assert "Validate, compare, and render benchmark evidence." in result.stdout


def test_help_is_available() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Validate, compare, and render benchmark evidence." in result.stdout


def test_version_is_available() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.startswith("benchpub ")
