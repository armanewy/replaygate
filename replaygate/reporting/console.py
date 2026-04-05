"""Console summary rendering."""

from __future__ import annotations

from rich.console import Console

from replaygate.models import VerificationReport
from replaygate.reporting.view_models import build_report_view


def render_console_summary(
    report: VerificationReport,
    *,
    mode: str = "default",
) -> str:
    view = build_report_view(report, top_failures_limit=10 if mode == "verbose" else 5)

    if mode == "quiet":
        lines = [
            (
                f"{view.verdict} histories={view.histories_checked} "
                f"passed={view.passed} failed={view.failed} "
                f"skipped={view.skipped} errors={view.errored}"
            )
        ]
        if view.artifacts:
            artifact_summary = ", ".join(
                f"{artifact.label}={artifact.path}" for artifact in view.artifacts
            )
            lines.append(f"Artifacts: {artifact_summary}")
        return "\n".join(lines)

    lines = [
        f"Replay Gate {view.tool_version}",
        f"Project: {view.project_name}",
        f"Engine: {view.engine}",
        f"Config: {view.config_path}",
    ]
    if view.git_sha is not None:
        lines.append(f"Git SHA: {view.git_sha}")

    lines.extend(
        [
            "",
            f"VERDICT: {view.verdict}",
            f"Policy decision: {view.policy_decision}",
            f"Histories checked: {view.histories_checked}",
            (
                f"Passed: {view.passed}  Failed: {view.failed}  "
                f"Skipped: {view.skipped}  Errors: {view.errored}"
            ),
        ]
    )

    lines.extend(["", "Policy violations:"])
    if view.violations:
        for rule in view.violations:
            lines.append(f"- {rule}")
    else:
        lines.append("- none")

    lines.extend(["", "Failure breakdown:"])
    if view.failure_breakdown:
        for item in view.failure_breakdown:
            lines.append(f"- {item.label}: {item.count}")
    else:
        lines.append("- none")

    if mode == "verbose":
        lines.extend(["", "Workflow type breakdown:"])
        for row in view.workflow_breakdown:
            dominant = (
                row.dominant_failure_kind.value if row.dominant_failure_kind is not None else "none"
            )
            lines.append(
                f"- {row.workflow_type}: checked={row.checked} passed={row.passed} "
                f"failed={row.failed} skipped={row.skipped} errors={row.errored} "
                f"dominant={dominant} risk={row.risk_level.value}"
            )

    lines.extend(["", "Top failing histories:"])
    if view.top_failures:
        for index, result in enumerate(view.top_failures, start=1):
            lines.extend(
                [
                    f"{index}. {result.path}",
                    f"   workflow: {result.workflow_type}",
                    f"   kind: {result.failure_kind}",
                    f"   summary: {result.summary}",
                    f"   hint: {result.remediation_hint or '-'}",
                ]
            )
            if mode == "verbose":
                lines.append(f"   likely cause: {result.likely_cause or '-'}")
    else:
        lines.append("- none")

    lines.extend(["", "Artifacts:"])
    if view.artifacts:
        for artifact in view.artifacts:
            lines.append(f"- {artifact.label}: {artifact.path}")
    else:
        lines.append("- none")

    return "\n".join(lines)


def print_console_summary(
    report: VerificationReport,
    console: Console | None = None,
    *,
    mode: str = "default",
) -> None:
    sink = console or Console()
    view = build_report_view(report)
    style = {
        "PASSED": "bold green",
        "FAILED": "bold red",
        "ERROR": "bold red",
    }.get(view.verdict, "bold yellow")
    sink.print(render_console_summary(report, mode=mode), style=style)
