"""CLI entry point for Replay Gate."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from replaygate.config import default_config_template, load_config

app = typer.Typer(help="Replay Gate durable workflow deployment safety checks.")


@app.command()
def init(
    output: Path = typer.Option(
        Path("replaygate.yaml"),
        "--output",
        "-o",
        help="Where to write a starter config file.",
    ),
) -> None:
    """Write a starter config file."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(default_config_template(), encoding="utf-8")
    typer.echo(f"Wrote starter config to {output}")


@app.command()
def verify(
    config: Path = typer.Option(..., "--config", "-c", exists=True, dir_okay=False),
) -> None:
    """Validate config and show the selected engine.

    Full verification wiring lands in the next milestones.
    """
    loaded = load_config(config)
    typer.echo(
        f"Loaded config for project={loaded.project.name} engine={loaded.project.engine.value}"
    )


@app.command()
def explain(
    report: Path = typer.Option(..., "--report", "-r", exists=True, dir_okay=False),
) -> None:
    """Pretty-print a generated JSON report."""
    payload = json.loads(report.read_text(encoding="utf-8"))
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    app()
