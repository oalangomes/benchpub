"""Public command-line interface for benchpub."""

from pathlib import Path
from typing import Annotated

import typer

from benchpub import __version__
from benchpub.validation import validate_file

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
        typer.echo(f"✗ {path}")
        for issue in result.issues:
            typer.echo(f"  {issue.path}: {issue.message}")

    if invalid_count:
        raise typer.Exit(code=1)

    count = len(files)
    noun = "manifest" if count == 1 else "manifests"
    typer.echo(f"\n{count} valid benchmark result {noun}")
