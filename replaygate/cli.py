"""CLI entry point for Replay Gate."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from replaygate.config import default_config_template
from replaygate.models import ReplayStatus, VerificationReport
from replaygate.reporting.console import print_console_summary
from replaygate.verifier import verify_config

app = typer.Typer(help="Replay Gate durable workflow deployment safety checks.")
OUTPUT_OPTION = typer.Option(
    Path("replaygate.yaml"),
    "--output",
    "-o",
    help="Where to write a starter config file.",
)
CONFIG_OPTION = typer.Option(..., "--config", "-c", exists=True, dir_okay=False)
REPORT_OPTION = typer.Option(..., "--report", "-r", exists=True, dir_okay=False)


@app.command()
def init(output: Path = OUTPUT_OPTION) -> None:
    """Write a starter config file."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(default_config_template(), encoding="utf-8")
    typer.echo(f"Wrote starter config to {output}")


@app.command()
def verify(config: Path = CONFIG_OPTION) -> None:
    """Run replay verification against the configured histories and candidate workflows."""
    console = Console()
    try:
        execution = asyncio.run(verify_config(config))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        console.print(f"Replay Gate: ERROR\n{exc}", style="bold red")
        raise typer.Exit(code=2) from exc
    print_console_summary(execution.report, console)
    if execution.written_outputs:
        console.print("")
        console.print("Artifacts:")
        for name, path in execution.written_outputs.items():
            console.print(f"- {name}: {path}")
    raise typer.Exit(code=execution.exit_code)


@app.command()
def explain(report: Path = REPORT_OPTION) -> None:
    """Pretty-print a generated JSON report."""
    console = Console()
    loaded = VerificationReport.model_validate_json(report.read_text(encoding="utf-8"))

    failures = [
        result
        for result in loaded.results
        if result.status in {ReplayStatus.FAILED, ReplayStatus.ERROR} and result.failure is not None
    ]
    if not failures:
        console.print("Report contains no failures.", style="green")
        return

    for index, result in enumerate(failures, start=1):
        console.print(
            f"{index}. {result.workflow_type or 'unknown-workflow'} / {result.artifact.path}\n"
            f"   kind: {result.failure.kind.value}\n"
            f"   summary: {result.failure.summary}\n"
            f"   likely cause: {result.failure.likely_cause}\n"
            f"   remediation: {result.failure.remediation_hint}"
        )


if __name__ == "__main__":
    app()
