"""Manifest loading and validation helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from benchpub.models import BenchmarkResult


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str


@dataclass(frozen=True)
class FileValidation:
    path: Path
    manifest: BenchmarkResult | None
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return self.manifest is not None and not self.issues


def _format_location(location: tuple[object, ...]) -> str:
    return ".".join(str(part) for part in location) or "<root>"


def validate_file(path: Path) -> FileValidation:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return FileValidation(
            path=path,
            manifest=None,
            issues=(ValidationIssue("<file>", str(exc)),),
        )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return FileValidation(
            path=path,
            manifest=None,
            issues=(
                ValidationIssue(
                    "<json>",
                    f"{exc.msg} at line {exc.lineno}, column {exc.colno}",
                ),
            ),
        )

    try:
        manifest = BenchmarkResult.model_validate(data)
    except ValidationError as exc:
        issues = tuple(
            ValidationIssue(
                _format_location(error["loc"]),
                error["msg"],
            )
            for error in exc.errors()
        )
        return FileValidation(path=path, manifest=None, issues=issues)

    return FileValidation(path=path, manifest=manifest, issues=())
