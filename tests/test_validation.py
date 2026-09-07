from pathlib import Path

from benchpub.validation import validate_file


def test_validation_reports_exact_nested_path(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(
        '{"schema_version":1,"experiment":{"id":"x"},'
        '"metrics":[{"name":"latency","value":"fast"}]}',
        encoding="utf-8",
    )

    result = validate_file(path)

    assert not result.is_valid
    assert [issue.path for issue in result.issues] == ["metrics.0.value"]


def test_validation_reports_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text('{"schema_version":', encoding="utf-8")

    result = validate_file(path)

    assert not result.is_valid
    assert result.issues[0].path == "<json>"
    assert "line 1" in result.issues[0].message


def test_validation_reports_missing_file(tmp_path: Path) -> None:
    result = validate_file(tmp_path / "missing.json")

    assert not result.is_valid
    assert result.issues[0].path == "<file>"
