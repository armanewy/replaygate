"""Console summary rendering."""

from __future__ import annotations

from rich.console import Console

from replaygate.models import ReplayStatus, VerificationReport


def render_console_summary(report: VerificationReport) -> str:
    status = "PASSED" if report.policy.passed else "FAILED"
    lines = [
        f"Replay Gate: {status}",
        f"Project: {report.project_name}",
        f"Engine: {report.engine.value}",
        f"Histories checked: {report.summary.total_histories}",
        f"Passed: {report.summary.passed}",
        f"Failed: {report.summary.failed}",
        f"Errors: {report.summary.errors}",
        f"Skipped: {report.summary.skipped}",
    ]

    failures = [
        result
        for result in report.results
        if result.status in {ReplayStatus.FAILED, ReplayStatus.ERROR} and result.failure is not None
    ]
    if failures:
        lines.append("")
        lines.append("Top failures:")
        for index, result in enumerate(failures[:5], start=1):
            label = f"{result.workflow_type or 'unknown-workflow'} / {result.artifact.path}"
            lines.extend(
                [
                    f"{index}. {label}",
                    f"   kind: {result.failure.kind.value}",
                    f"   summary: {result.failure.summary}",
                ]
            )

    lines.append("")
    lines.append("Policy:")
    if report.policy.violated_rules:
        for rule in report.policy.violated_rules:
            lines.append(f"- {rule}")
    else:
        lines.append("- all checks passed")

    return "\n".join(lines)


def print_console_summary(report: VerificationReport, console: Console | None = None) -> None:
    sink = console or Console()
    style = "bold green" if report.policy.passed else "bold red"
    sink.print(render_console_summary(report), style=style)
