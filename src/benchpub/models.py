"""Versioned public result models for benchpub."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StrictFloat,
    StringConstraints,
    field_validator,
)

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
MetricValue = StrictFloat


class Experiment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString
    name: NonEmptyString | None = None
    hypothesis: NonEmptyString | None = None
    variant: NonEmptyString | None = None


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyString
    revision: NonEmptyString | None = None


class Metric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyString
    value: MetricValue
    unit: NonEmptyString | None = None
    direction: Literal["higher", "lower", "none"] | None = None

    @field_validator("value")
    @classmethod
    def value_must_be_finite(cls, value: MetricValue) -> MetricValue:
        if not math.isfinite(float(value)):
            raise ValueError("metric value must be finite")
        return value


class GitProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    commit: NonEmptyString
    dirty: bool | None = None


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime | None = None
    git: GitProvenance | None = None


class BenchmarkResult(BaseModel):
    """A single benchmark result manifest using schema version 1."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    experiment: Experiment
    metrics: list[Metric] = Field(min_length=1)
    dataset: Dataset | None = None
    controlled_variables: dict[str, JsonValue] | None = None
    configuration: dict[str, JsonValue] | None = None
    environment: dict[str, JsonValue] | None = None
    provenance: Provenance | None = None
    artifacts: list[NonEmptyString] | None = None
    notes: str | None = None

    @field_validator("metrics")
    @classmethod
    def metric_names_must_be_unique(cls, metrics: list[Metric]) -> list[Metric]:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for metric in metrics:
            if metric.name in seen:
                duplicates.add(metric.name)
            seen.add(metric.name)

        if duplicates:
            joined = ", ".join(sorted(duplicates))
            raise ValueError(f"metric names must be unique; duplicates: {joined}")
        return metrics
