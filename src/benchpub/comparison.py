"""Deterministic comparison of two validated benchmark result manifests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from benchpub.models import BenchmarkResult, Metric


class Comparability(StrEnum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    INDETERMINATE = "indeterminate"


class FindingKind(StrEnum):
    DIFFERENT = "different"
    MISSING_BASELINE = "missing_baseline"
    MISSING_TREATMENT = "missing_treatment"


class MetricOutcome(StrEnum):
    IMPROVED = "improved"
    REGRESSED = "regressed"
    UNCHANGED = "unchanged"
    NOT_EVALUATED = "not_evaluated"


@dataclass(frozen=True)
class ComparabilityFinding:
    path: str
    kind: FindingKind
    baseline: Any
    treatment: Any


@dataclass(frozen=True)
class ComparisonWarning:
    code: str
    message: str
    metric: str | None = None


@dataclass(frozen=True)
class MetricComparison:
    name: str
    unit: str | None
    baseline: float
    treatment: float
    delta: float | None
    relative_delta_percent: float | None
    direction: str | None
    outcome: MetricOutcome
    comparable: bool
    reason: str | None = None


@dataclass(frozen=True)
class ComparisonResult:
    experiment_id: str
    comparability: Comparability
    findings: tuple[ComparabilityFinding, ...]
    metrics: tuple[MetricComparison, ...]
    warnings: tuple[ComparisonWarning, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _compare_declared_value(
    path: str,
    *,
    baseline_present: bool,
    baseline: Any,
    treatment_present: bool,
    treatment: Any,
) -> ComparabilityFinding | None:
    if not baseline_present and not treatment_present:
        return None
    if not baseline_present:
        return ComparabilityFinding(path, FindingKind.MISSING_BASELINE, None, treatment)
    if not treatment_present:
        return ComparabilityFinding(path, FindingKind.MISSING_TREATMENT, baseline, None)
    if baseline != treatment:
        return ComparabilityFinding(path, FindingKind.DIFFERENT, baseline, treatment)
    return None


def _comparability_findings(
    baseline: BenchmarkResult,
    treatment: BenchmarkResult,
) -> tuple[ComparabilityFinding, ...]:
    findings: list[ComparabilityFinding] = []

    if baseline.experiment.id != treatment.experiment.id:
        findings.append(
            ComparabilityFinding(
                "experiment.id",
                FindingKind.DIFFERENT,
                baseline.experiment.id,
                treatment.experiment.id,
            )
        )

    baseline_dataset = baseline.dataset
    treatment_dataset = treatment.dataset
    if baseline_dataset is None or treatment_dataset is None:
        finding = _compare_declared_value(
            "dataset",
            baseline_present=baseline_dataset is not None,
            baseline=(
                baseline_dataset.model_dump(mode="json") if baseline_dataset is not None else None
            ),
            treatment_present=treatment_dataset is not None,
            treatment=(
                treatment_dataset.model_dump(mode="json") if treatment_dataset is not None else None
            ),
        )
        if finding is not None:
            findings.append(finding)
    else:
        if baseline_dataset.name != treatment_dataset.name:
            findings.append(
                ComparabilityFinding(
                    "dataset.name",
                    FindingKind.DIFFERENT,
                    baseline_dataset.name,
                    treatment_dataset.name,
                )
            )
        revision_finding = _compare_declared_value(
            "dataset.revision",
            baseline_present=baseline_dataset.revision is not None,
            baseline=baseline_dataset.revision,
            treatment_present=treatment_dataset.revision is not None,
            treatment=treatment_dataset.revision,
        )
        if revision_finding is not None:
            findings.append(revision_finding)

    baseline_controls = baseline.controlled_variables or {}
    treatment_controls = treatment.controlled_variables or {}
    for key in sorted(baseline_controls.keys() | treatment_controls.keys()):
        finding = _compare_declared_value(
            f"controlled_variables.{key}",
            baseline_present=key in baseline_controls,
            baseline=baseline_controls.get(key),
            treatment_present=key in treatment_controls,
            treatment=treatment_controls.get(key),
        )
        if finding is not None:
            findings.append(finding)

    return tuple(findings)


def _comparability_state(findings: tuple[ComparabilityFinding, ...]) -> Comparability:
    if any(finding.kind is FindingKind.DIFFERENT for finding in findings):
        return Comparability.INCOMPATIBLE
    if findings:
        return Comparability.INDETERMINATE
    return Comparability.COMPATIBLE


def _outcome(delta: float, direction: str | None) -> MetricOutcome:
    if delta == 0:
        return MetricOutcome.UNCHANGED
    if direction == "higher":
        return MetricOutcome.IMPROVED if delta > 0 else MetricOutcome.REGRESSED
    if direction == "lower":
        return MetricOutcome.IMPROVED if delta < 0 else MetricOutcome.REGRESSED
    return MetricOutcome.NOT_EVALUATED


def _compare_metric(
    baseline: Metric,
    treatment: Metric,
) -> tuple[MetricComparison, tuple[ComparisonWarning, ...]]:
    warnings: list[ComparisonWarning] = []

    if baseline.unit != treatment.unit:
        warnings.append(
            ComparisonWarning(
                code="unit_mismatch",
                metric=baseline.name,
                message=(
                    f"metric {baseline.name!r} has different units: "
                    f"baseline={baseline.unit!r}, treatment={treatment.unit!r}"
                ),
            )
        )
        return (
            MetricComparison(
                name=baseline.name,
                unit=None,
                baseline=baseline.value,
                treatment=treatment.value,
                delta=None,
                relative_delta_percent=None,
                direction=None,
                outcome=MetricOutcome.NOT_EVALUATED,
                comparable=False,
                reason="unit_mismatch",
            ),
            tuple(warnings),
        )

    direction = baseline.direction if baseline.direction == treatment.direction else None
    if baseline.direction != treatment.direction:
        warnings.append(
            ComparisonWarning(
                code="direction_mismatch",
                metric=baseline.name,
                message=(
                    f"metric {baseline.name!r} has different directions: "
                    f"baseline={baseline.direction!r}, treatment={treatment.direction!r}"
                ),
            )
        )

    delta = treatment.value - baseline.value
    relative_delta_percent = None if baseline.value == 0 else (delta / baseline.value) * 100

    return (
        MetricComparison(
            name=baseline.name,
            unit=baseline.unit,
            baseline=baseline.value,
            treatment=treatment.value,
            delta=delta,
            relative_delta_percent=relative_delta_percent,
            direction=direction,
            outcome=_outcome(delta, direction),
            comparable=True,
        ),
        tuple(warnings),
    )


def compare_results(
    baseline: BenchmarkResult,
    treatment: BenchmarkResult,
) -> ComparisonResult:
    findings = _comparability_findings(baseline, treatment)
    warnings: list[ComparisonWarning] = []
    metrics: list[MetricComparison] = []

    baseline_metrics = {metric.name: metric for metric in baseline.metrics}
    treatment_metrics = {metric.name: metric for metric in treatment.metrics}

    for name in sorted(baseline_metrics.keys() | treatment_metrics.keys()):
        baseline_metric = baseline_metrics.get(name)
        treatment_metric = treatment_metrics.get(name)

        if baseline_metric is None:
            warnings.append(
                ComparisonWarning(
                    code="metric_missing_baseline",
                    metric=name,
                    message=f"metric {name!r} is missing from baseline",
                )
            )
            continue
        if treatment_metric is None:
            warnings.append(
                ComparisonWarning(
                    code="metric_missing_treatment",
                    metric=name,
                    message=f"metric {name!r} is missing from treatment",
                )
            )
            continue

        metric_comparison, metric_warnings = _compare_metric(baseline_metric, treatment_metric)
        metrics.append(metric_comparison)
        warnings.extend(metric_warnings)

    return ComparisonResult(
        experiment_id=baseline.experiment.id,
        comparability=_comparability_state(findings),
        findings=findings,
        metrics=tuple(metrics),
        warnings=tuple(warnings),
    )
