import math

import pytest
from pydantic import ValidationError

from benchpub.models import BenchmarkResult


def minimal_manifest() -> dict[str, object]:
    return {
        "schema_version": 1,
        "experiment": {"id": "lookup-001"},
        "metrics": [{"name": "latency_ms", "value": 12.4}],
    }


def test_minimal_manifest_is_valid() -> None:
    result = BenchmarkResult.model_validate(minimal_manifest())

    assert result.schema_version == 1
    assert result.experiment.id == "lookup-001"
    assert result.metrics[0].value == 12.4


def test_optional_evidence_fields_are_supported() -> None:
    manifest = minimal_manifest()
    manifest.update(
        {
            "dataset": {"name": "sample", "revision": "v1"},
            "controlled_variables": {"top_k": 20, "nested": {"enabled": True}},
            "configuration": {"strategy": "lexical"},
            "environment": {"python": "3.13"},
            "provenance": {
                "timestamp": "2026-09-07T18:00:00Z",
                "git": {"commit": "abc123", "dirty": False},
            },
            "artifacts": ["raw/results.json"],
            "notes": "Focused run",
        }
    )

    result = BenchmarkResult.model_validate(manifest)

    assert result.dataset is not None
    assert result.dataset.revision == "v1"
    assert result.provenance is not None
    assert result.provenance.git is not None
    assert result.provenance.git.commit == "abc123"


def test_unknown_top_level_field_is_rejected() -> None:
    manifest = minimal_manifest()
    manifest["surprise"] = True

    with pytest.raises(ValidationError):
        BenchmarkResult.model_validate(manifest)


def test_boolean_schema_version_is_rejected() -> None:
    manifest = minimal_manifest()
    manifest["schema_version"] = True

    with pytest.raises(ValidationError, match="schema_version must be the integer 1"):
        BenchmarkResult.model_validate(manifest)


def test_string_git_dirty_flag_is_rejected() -> None:
    manifest = minimal_manifest()
    manifest["provenance"] = {"git": {"commit": "abc123", "dirty": "false"}}

    with pytest.raises(ValidationError):
        BenchmarkResult.model_validate(manifest)


def test_numeric_timestamp_is_rejected() -> None:
    manifest = minimal_manifest()
    manifest["provenance"] = {"timestamp": 0}

    with pytest.raises(ValidationError, match="timestamp must be an ISO 8601 string"):
        BenchmarkResult.model_validate(manifest)


def test_schema_version_other_than_one_is_rejected() -> None:
    manifest = minimal_manifest()
    manifest["schema_version"] = 2

    with pytest.raises(ValidationError):
        BenchmarkResult.model_validate(manifest)


def test_metrics_must_not_be_empty() -> None:
    manifest = minimal_manifest()
    manifest["metrics"] = []

    with pytest.raises(ValidationError):
        BenchmarkResult.model_validate(manifest)


def test_metric_names_must_be_unique() -> None:
    manifest = minimal_manifest()
    manifest["metrics"] = [
        {"name": "recall", "value": 0.7},
        {"name": "recall", "value": 0.8},
    ]

    with pytest.raises(ValidationError, match="metric names must be unique"):
        BenchmarkResult.model_validate(manifest)


def test_integer_metric_value_is_accepted_as_a_json_number() -> None:
    manifest = minimal_manifest()
    manifest["metrics"] = [{"name": "requests", "value": 12}]

    result = BenchmarkResult.model_validate(manifest)

    assert result.metrics[0].value == 12.0


def test_metric_value_must_be_a_json_number_not_a_string() -> None:
    manifest = minimal_manifest()
    manifest["metrics"] = [{"name": "latency_ms", "value": "12.4"}]

    with pytest.raises(ValidationError):
        BenchmarkResult.model_validate(manifest)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_metric_value_must_be_finite(value: float) -> None:
    manifest = minimal_manifest()
    manifest["metrics"] = [{"name": "latency_ms", "value": value}]

    with pytest.raises(ValidationError, match="metric value must be finite"):
        BenchmarkResult.model_validate(manifest)
