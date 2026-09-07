import json

import pytest

from benchpub.comparison import (
    Comparability,
    FindingKind,
    MetricOutcome,
    compare_results,
)
from benchpub.models import BenchmarkResult


def result(
    *,
    experiment_id: str = "exp-1",
    metrics: list[dict[str, object]] | None = None,
    dataset: dict[str, object] | None = None,
    controls: dict[str, object] | None = None,
) -> BenchmarkResult:
    data: dict[str, object] = {
        "schema_version": 1,
        "experiment": {"id": experiment_id},
        "metrics": metrics or [{"name": "score", "value": 10.0}],
    }
    if dataset is not None:
        data["dataset"] = dataset
    if controls is not None:
        data["controlled_variables"] = controls
    return BenchmarkResult.model_validate(data)


def test_identical_declared_evidence_is_compatible() -> None:
    baseline = result(dataset={"name": "corpus", "revision": "v1"}, controls={"k": 20})
    treatment = result(dataset={"name": "corpus", "revision": "v1"}, controls={"k": 20})

    comparison = compare_results(baseline, treatment)

    assert comparison.comparability is Comparability.COMPATIBLE
    assert comparison.findings == ()


def test_different_experiment_ids_are_incompatible() -> None:
    comparison = compare_results(result(experiment_id="a"), result(experiment_id="b"))

    assert comparison.comparability is Comparability.INCOMPATIBLE
    assert comparison.findings[0].path == "experiment.id"
    assert comparison.findings[0].kind is FindingKind.DIFFERENT


def test_different_control_is_incompatible() -> None:
    comparison = compare_results(result(controls={"k": 20}), result(controls={"k": 40}))

    assert comparison.comparability is Comparability.INCOMPATIBLE
    assert comparison.findings[0].path == "controlled_variables.k"


def test_missing_control_is_indeterminate() -> None:
    comparison = compare_results(result(controls={"k": 20}), result())

    assert comparison.comparability is Comparability.INDETERMINATE
    assert comparison.findings[0].kind is FindingKind.MISSING_TREATMENT


def test_dataset_name_difference_is_incompatible() -> None:
    comparison = compare_results(
        result(dataset={"name": "a", "revision": "v1"}),
        result(dataset={"name": "b", "revision": "v1"}),
    )

    assert comparison.comparability is Comparability.INCOMPATIBLE
    assert any(finding.path == "dataset.name" for finding in comparison.findings)


def test_dataset_revision_difference_is_incompatible() -> None:
    comparison = compare_results(
        result(dataset={"name": "a", "revision": "v1"}),
        result(dataset={"name": "a", "revision": "v2"}),
    )

    assert comparison.comparability is Comparability.INCOMPATIBLE
    assert any(finding.path == "dataset.revision" for finding in comparison.findings)


def test_missing_dataset_on_one_side_is_indeterminate() -> None:
    comparison = compare_results(result(dataset={"name": "a"}), result())

    assert comparison.comparability is Comparability.INDETERMINATE
    assert comparison.findings[0].path == "dataset"


def test_metric_delta_and_relative_change_are_computed() -> None:
    comparison = compare_results(
        result(metrics=[{"name": "recall", "value": 0.5, "direction": "higher"}]),
        result(metrics=[{"name": "recall", "value": 0.75, "direction": "higher"}]),
    )

    metric = comparison.metrics[0]
    assert metric.delta == pytest.approx(0.25)
    assert metric.relative_delta_percent == pytest.approx(50.0)
    assert metric.outcome is MetricOutcome.IMPROVED


def test_lower_direction_can_improve_with_negative_delta() -> None:
    comparison = compare_results(
        result(metrics=[{"name": "latency", "value": 100, "unit": "ms", "direction": "lower"}]),
        result(metrics=[{"name": "latency", "value": 80, "unit": "ms", "direction": "lower"}]),
    )

    assert comparison.metrics[0].outcome is MetricOutcome.IMPROVED


def test_zero_baseline_has_no_relative_delta() -> None:
    comparison = compare_results(
        result(metrics=[{"name": "errors", "value": 0}]),
        result(metrics=[{"name": "errors", "value": 1}]),
    )

    assert comparison.metrics[0].delta == 1
    assert comparison.metrics[0].relative_delta_percent is None


def test_no_direction_does_not_claim_improvement() -> None:
    comparison = compare_results(
        result(metrics=[{"name": "score", "value": 10}]),
        result(metrics=[{"name": "score", "value": 12}]),
    )

    assert comparison.metrics[0].outcome is MetricOutcome.NOT_EVALUATED


def test_equal_values_are_unchanged_even_without_direction() -> None:
    comparison = compare_results(result(), result())

    assert comparison.metrics[0].outcome is MetricOutcome.UNCHANGED


def test_unit_mismatch_prevents_metric_delta() -> None:
    comparison = compare_results(
        result(metrics=[{"name": "latency", "value": 1, "unit": "s"}]),
        result(metrics=[{"name": "latency", "value": 1000, "unit": "ms"}]),
    )

    metric = comparison.metrics[0]
    assert not metric.comparable
    assert metric.delta is None
    assert metric.reason == "unit_mismatch"
    assert comparison.warnings[0].code == "unit_mismatch"


def test_missing_metric_is_reported_as_warning() -> None:
    comparison = compare_results(
        result(metrics=[{"name": "recall", "value": 0.5}]),
        result(metrics=[{"name": "latency", "value": 10}]),
    )

    assert comparison.metrics == ()
    assert {warning.code for warning in comparison.warnings} == {
        "metric_missing_baseline",
        "metric_missing_treatment",
    }


def test_direction_mismatch_keeps_delta_but_not_outcome_claim() -> None:
    comparison = compare_results(
        result(metrics=[{"name": "score", "value": 10, "direction": "higher"}]),
        result(metrics=[{"name": "score", "value": 12, "direction": "none"}]),
    )

    metric = comparison.metrics[0]
    assert metric.delta == 2
    assert metric.direction is None
    assert metric.outcome is MetricOutcome.NOT_EVALUATED
    assert comparison.warnings[0].code == "direction_mismatch"


def test_json_dict_is_serializable_and_uses_string_enum_values() -> None:
    comparison = compare_results(result(), result())

    payload = comparison.to_dict()

    assert payload["comparability"] == "compatible"
    assert payload["metrics"][0]["outcome"] == "unchanged"


def test_declared_null_control_is_distinct_from_missing_control() -> None:
    comparison = compare_results(result(controls={"seed": None}), result())

    assert comparison.comparability is Comparability.INDETERMINATE
    assert comparison.findings[0].path == "controlled_variables.seed"
    assert comparison.findings[0].kind is FindingKind.MISSING_TREATMENT


def test_missing_dataset_finding_is_json_serializable() -> None:
    comparison = compare_results(result(dataset={"name": "corpus"}), result())

    json.dumps(comparison.to_dict())
