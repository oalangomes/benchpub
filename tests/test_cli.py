from pathlib import Path

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


def test_validate_accepts_valid_manifest(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    path.write_text(
        '{"schema_version":1,"experiment":{"id":"x"},'
        '"metrics":[{"name":"recall","value":0.8}]}',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", str(path)])

    assert result.exit_code == 0
    assert f"✓ {path}" in result.stdout
    assert "1 valid benchmark result manifest" in result.stdout


def test_validate_rejects_invalid_manifest_with_path(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    path.write_text(
        '{"schema_version":1,"experiment":{"id":"x"},'
        '"metrics":[{"name":"recall","value":"high"}]}',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", str(path)])

    assert result.exit_code == 1
    assert f"✗ {path}" in result.stdout
    assert "metrics.0.value" in result.stdout
