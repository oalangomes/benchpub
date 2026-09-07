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


def test_validation_reports_non_utf8_json(tmp_path: Path) -> None:
    path = tmp_path / "binary.json"
    path.write_bytes(b'{"value":"\xff"}')

    result = validate_file(path)

    assert not result.is_valid
    assert result.issues[0].path == "<encoding>"


def test_valid_result_retains_exact_validated_bytes(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    source = (
        b'{"schema_version":1,"experiment":{"id":"x"},'
        b'"metrics":[{"name":"score","value":1}]}\n'
    )
    path.write_bytes(source)

    result = validate_file(path)

    assert result.is_valid
    assert result.source_bytes == source
