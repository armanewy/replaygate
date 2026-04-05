"""CLI entry point for Replay Gate."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from pydantic import ValidationError
from rich.console import Console

from replaygate.config import default_config_template
from replaygate.models import ReplayStatus, VerificationReport, WorkflowEngine
from replaygate.reporting.console import print_console_summary
from replaygate.reporting.html_report import write_html_report
from replaygate.reporting.json_report import render_json_report
from replaygate.reporting.markdown_report import write_markdown_report
from replaygate.verifier import verify_config

app = typer.Typer(help="Replay Gate durable workflow deployment safety checks.")
OUTPUT_OPTION = typer.Option(
    Path("replaygate.yaml"),
    "--output",
    "-o",
    help="Where to write a starter config file.",
)
ENGINE_OPTION = typer.Option(WorkflowEngine.TEMPORAL, "--engine")
CONFIG_OPTION = typer.Option(..., "--config", "-c", exists=True, dir_okay=False)
REPORT_OPTION = typer.Option(..., "--report", "-r", exists=True, dir_okay=False)
INPUT_OPTION = typer.Option(..., "--input", "-i", exists=True, dir_okay=False)
MARKDOWN_OPTION = typer.Option(None, "--markdown", help="Write markdown output.")
HTML_OPTION = typer.Option(None, "--html", help="Write HTML output.")
CONSOLE_OPTION = typer.Option(False, "--console", help="Print console summary.")


@app.command()
def init(
    output: Path = OUTPUT_OPTION,
    engine: WorkflowEngine = ENGINE_OPTION,
) -> None:
    """Write a starter config file."""
    if engine is not WorkflowEngine.TEMPORAL:
        raise typer.BadParameter("Only the Temporal engine is supported in the current MVP")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(default_config_template(), encoding="utf-8")
    (output.parent / "artifacts").mkdir(parents=True, exist_ok=True)
    (output.parent / "histories").mkdir(parents=True, exist_ok=True)
    typer.echo(f"Wrote starter config to {output}")
    typer.echo(f"Created {output.parent / 'artifacts'} and {output.parent / 'histories'}")
    typer.echo("Next step: replay-gate verify --config " + str(output))


@app.command()
def verify(
    config: Path = CONFIG_OPTION,
    quiet: bool = typer.Option(False, "--quiet", help="Print only verdict, counts, and artifacts."),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Print workflow breakdown and additional failure context.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON to stdout instead of console text.",
    ),
) -> None:
    """Run replay verification against the configured histories and candidate workflows."""
    if json_output and (quiet or verbose):
        raise typer.BadParameter("--json cannot be combined with --quiet or --verbose")
    if quiet and verbose:
        raise typer.BadParameter("Choose only one of --quiet or --verbose")

    console = Console()
    try:
        execution = asyncio.run(verify_config(config))
    except (ValidationError, ValueError, OSError) as exc:
        console.print(f"Replay Gate: CONFIG ERROR\n{exc}", style="bold red")
        raise typer.Exit(code=2) from exc
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        console.print(f"Replay Gate: INTERNAL ERROR\n{exc}", style="bold red")
        raise typer.Exit(code=4) from exc

    if json_output:
        typer.echo(render_json_report(execution.report), nl=False)
        raise typer.Exit(code=execution.exit_code)

    mode = "verbose" if verbose else "quiet" if quiet else "default"
    print_console_summary(execution.report, console, mode=mode)
    raise typer.Exit(code=execution.exit_code)


@app.command()
def report(
    input_path: Path = INPUT_OPTION,
    markdown: Path | None = MARKDOWN_OPTION,
    html: Path | None = HTML_OPTION,
    console_output: bool = CONSOLE_OPTION,
) -> None:
    """Re-render report artifacts from a stored JSON report."""
    console = Console()
    try:
        loaded = VerificationReport.model_validate_json(input_path.read_text(encoding="utf-8"))
    except (ValidationError, ValueError, OSError) as exc:
        console.print(f"Replay Gate: CONFIG ERROR\n{exc}", style="bold red")
        raise typer.Exit(code=2) from exc

    config_base_dir = Path(loaded.source.config_path).parent
    if markdown is None and loaded.artifacts.markdown_report is not None:
        markdown = config_base_dir / loaded.artifacts.markdown_report
    if html is None and loaded.artifacts.html_report is not None:
        html = config_base_dir / loaded.artifacts.html_report

    if markdown is not None:
        write_markdown_report(loaded, markdown)
        console.print(f"Wrote markdown report to {markdown}")
    if html is not None:
        write_html_report(loaded, html)
        console.print(f"Wrote HTML report to {html}")
    if console_output or (markdown is None and html is None):
        print_console_summary(loaded, console)


@app.command()
def explain(report: Path = REPORT_OPTION) -> None:
    """Pretty-print a generated JSON report."""
    console = Console()
    try:
        loaded = VerificationReport.model_validate_json(report.read_text(encoding="utf-8"))
    except (ValidationError, ValueError, OSError) as exc:
        console.print(f"Replay Gate: CONFIG ERROR\n{exc}", style="bold red")
        raise typer.Exit(code=2) from exc

    failures = [
        result
        for result in loaded.results
        if result.status in {ReplayStatus.FAILED, ReplayStatus.ERROR} and result.failure is not None
    ]
    if not failures:
        console.print("Report contains no failures.", style="green")
        return

    for index, result in enumerate(failures, start=1):
        failure = result.failure
        assert failure is not None
        console.print(
            f"{index}. {result.workflow_type or 'unknown-workflow'} / {result.artifact.path}\n"
            f"   kind: {failure.kind.value}\n"
            f"   summary: {failure.summary}\n"
            f"   likely cause: {failure.likely_cause}\n"
            f"   remediation: {failure.remediation_hint}"
        )


if __name__ == "__main__":
    app()
