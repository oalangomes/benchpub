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
    source_bytes: bytes | None = None

    @property
    def is_valid(self) -> bool:
        return self.manifest is not None and not self.issues


def _format_location(location: tuple[object, ...]) -> str:
    return ".".join(str(part) for part in location) or "<root>"


def validate_file(path: Path) -> FileValidation:
    try:
        source_bytes = path.read_bytes()
    except OSError as exc:
        return FileValidation(
            path=path,
            manifest=None,
            issues=(ValidationIssue("<file>", str(exc)),),
        )

    try:
        raw = source_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        return FileValidation(
            path=path,
            manifest=None,
            issues=(
                ValidationIssue(
                    "<encoding>",
                    f"file must be UTF-8 JSON: {exc}",
                ),
            ),
            source_bytes=source_bytes,
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
            source_bytes=source_bytes,
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
        return FileValidation(
            path=path,
            manifest=None,
            issues=issues,
            source_bytes=source_bytes,
        )

    return FileValidation(
        path=path,
        manifest=manifest,
        issues=(),
        source_bytes=source_bytes,
    )
