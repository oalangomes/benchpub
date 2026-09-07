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


def _write_result(path: Path, *, score: float, controls: str = "{}") -> None:
    path.write_text(
        '{"schema_version":1,"experiment":{"id":"exp-1"},'
        f'"controlled_variables":{controls},'
        f'"metrics":[{{"name":"score","value":{score},"direction":"higher"}}]}}',
        encoding="utf-8",
    )


def test_compare_human_output_reports_delta(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    treatment = tmp_path / "treatment.json"
    _write_result(baseline, score=10)
    _write_result(treatment, score=12)

    result = runner.invoke(app, ["compare", str(baseline), str(treatment)])

    assert result.exit_code == 0
    assert "Comparability: COMPATIBLE" in result.stdout
    assert "+2" in result.stdout
    assert "improved" in result.stdout


def test_compare_json_output_is_machine_readable(tmp_path: Path) -> None:
    import json

    baseline = tmp_path / "baseline.json"
    treatment = tmp_path / "treatment.json"
    _write_result(baseline, score=10)
    _write_result(treatment, score=12)

    result = runner.invoke(app, ["compare", str(baseline), str(treatment), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["comparability"] == "compatible"
    assert payload["metrics"][0]["delta"] == 2


def test_incompatible_comparison_is_a_successful_command_result(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    treatment = tmp_path / "treatment.json"
    _write_result(baseline, score=10, controls='{"k":20}')
    _write_result(treatment, score=12, controls='{"k":40}')

    result = runner.invoke(app, ["compare", str(baseline), str(treatment)])

    assert result.exit_code == 0
    assert "Comparability: INCOMPATIBLE" in result.stdout
    assert "controlled_variables.k" in result.stdout


def test_compare_rejects_invalid_input(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    treatment = tmp_path / "treatment.json"
    baseline.write_text("{}", encoding="utf-8")
    _write_result(treatment, score=12)

    result = runner.invoke(app, ["compare", str(baseline), str(treatment)])

    assert result.exit_code == 1
    assert f"✗ {baseline}" in result.stdout
