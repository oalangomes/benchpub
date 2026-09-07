"""Public command-line interface for benchpub."""

import json
from pathlib import Path
from typing import Annotated

import typer

from benchpub import __version__
from benchpub.comparison import ComparisonResult, compare_results
from benchpub.validation import FileValidation, validate_file

app = typer.Typer(
    name="benchpub",
    help="Validate, compare, and render benchmark evidence.",
    no_args_is_help=False,
    invoke_without_command=True,
    add_completion=False,
)


def _show_version(value: bool) -> None:
    if value:
        typer.echo(f"benchpub {__version__}")
        raise typer.Exit()


def _print_validation_failure(result: FileValidation) -> None:
    typer.echo(f"✗ {result.path}")
    for issue in result.issues:
        typer.echo(f"  {issue.path}: {issue.message}")


def _format_number(value: float | None, *, signed: bool = False) -> str:
    if value is None:
        return "N/A"
    prefix = "+" if signed and value > 0 else ""
    return f"{prefix}{value:.6g}"


def _format_change(value: float | None) -> str:
    if value is None:
        return "N/A"
    prefix = "+" if value > 0 else ""
    return f"{prefix}{value:.2f}%"


def _print_comparison(result: ComparisonResult) -> None:
    typer.echo(f"Experiment: {result.experiment_id}")
    typer.echo(f"Comparability: {result.comparability.value.upper()}")

    if result.findings:
        typer.echo("\nFindings:")
        for finding in result.findings:
            typer.echo(
                f"  - {finding.path}: {finding.kind.value} "
                f"(baseline={finding.baseline!r}, treatment={finding.treatment!r})"
            )

    if result.metrics:
        rows = []
        for metric in result.metrics:
            metric_name = f"{metric.name} [{metric.unit}]" if metric.unit else metric.name
            rows.append(
                (
                    metric_name,
                    _format_number(metric.baseline),
                    _format_number(metric.treatment),
                    _format_number(metric.delta, signed=True),
                    _format_change(metric.relative_delta_percent),
                    metric.outcome.value,
                )
            )

        headers = ("Metric", "Baseline", "Treatment", "Delta", "Change", "Outcome")
        widths = [
            max(len(headers[index]), *(len(row[index]) for row in rows))
            for index in range(len(headers))
        ]
        typer.echo("\nMetrics:")
        typer.echo("  " + "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
        typer.echo("  " + "  ".join("-" * width for width in widths))
        for row in rows:
            typer.echo("  " + "  ".join(value.ljust(widths[i]) for i, value in enumerate(row)))

    if result.warnings:
        typer.echo("\nWarnings:")
        for warning in result.warnings:
            typer.echo(f"  - [{warning.code}] {warning.message}")


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_show_version,
            is_eager=True,
            help="Show the benchpub version and exit.",
        ),
    ] = False,
) -> None:
    """Validate, compare, and render benchmark evidence."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def validate(
    files: Annotated[
        list[Path],
        typer.Argument(help="One or more benchmark result JSON files."),
    ],
) -> None:
    """Validate benchmark result manifests against schema v1."""
    invalid_count = 0

    for path in files:
        result = validate_file(path)
        if result.is_valid:
            typer.echo(f"✓ {path}")
            continue

        invalid_count += 1
        _print_validation_failure(result)

    if invalid_count:
        raise typer.Exit(code=1)

    count = len(files)
    noun = "manifest" if count == 1 else "manifests"
    typer.echo(f"\n{count} valid benchmark result {noun}")


@app.command()
def compare(
    baseline: Annotated[Path, typer.Argument(help="Baseline result JSON file.")],
    treatment: Annotated[Path, typer.Argument(help="Treatment result JSON file.")],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON."),
    ] = False,
) -> None:
    """Compare baseline and treatment benchmark results."""
    baseline_validation = validate_file(baseline)
    treatment_validation = validate_file(treatment)

    invalid = False
    for validation in (baseline_validation, treatment_validation):
        if not validation.is_valid:
            invalid = True
            _print_validation_failure(validation)
    if invalid:
        raise typer.Exit(code=1)

    assert baseline_validation.manifest is not None
    assert treatment_validation.manifest is not None
    result = compare_results(baseline_validation.manifest, treatment_validation.manifest)

    if json_output:
        typer.echo(json.dumps(result.to_dict(), indent=2, sort_keys=True, ensure_ascii=False))
        return

    _print_comparison(result)
