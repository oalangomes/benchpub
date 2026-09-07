"""Public command-line interface for benchpub."""

from typing import Annotated

import typer

from benchpub import __version__

app = typer.Typer(
    name="benchpub",
    help="Validate, compare, and render benchmark evidence.",
    no_args_is_help=True,
    add_completion=False,
)


def _show_version(value: bool) -> None:
    if value:
        typer.echo(f"benchpub {__version__}")
        raise typer.Exit()


@app.callback()
def main(
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
