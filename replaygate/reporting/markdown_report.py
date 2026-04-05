"""Markdown and GitHub summary rendering."""

from __future__ import annotations

from pathlib import Path

from replaygate.models import VerificationReport
from replaygate.reporting.view_models import build_report_view


def render_markdown_report(report: VerificationReport) -> str:
    view = build_report_view(report)
    lines = [
        f"## Replay Gate — {view.verdict}",
        f"**Tool:** {view.tool_version}  ",
        f"**Project:** {view.project_name}  ",
        f"**Engine:** {view.engine}  ",
        f"**Config:** `{view.config_path}`  ",
    ]
    if view.git_sha is not None:
        lines.append(f"**Git SHA:** `{view.git_sha}`  ")
    lines.extend(
        [
            f"**Histories checked:** {view.histories_checked}  ",
            f"**Passed:** {view.passed}  ",
            f"**Failed:** {view.failed}  ",
            f"**Skipped:** {view.skipped}  ",
            f"**Errors:** {view.errored}  ",
            f"**Workflow types covered:** {view.workflow_types}",
            "",
            "### Policy decision",
            view.policy_summary,
            "",
        ]
    )

    if view.violations:
        lines.append("Violations:")
        for rule in view.violations:
            lines.append(f"- `{rule}`")
    else:
        lines.append("Violations:")
        lines.append("- none")

    lines.extend(["", "### Failure breakdown"])
    if view.failure_breakdown:
        for item in view.failure_breakdown:
            lines.append(f"- {item.label}: {item.count}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "### Workflow type breakdown",
            "",
            (
                "| Workflow type | Checked | Passed | Failed | Skipped | "
                "Errors | Dominant failure | Risk | Notes |"
            ),
            "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for row in view.workflow_breakdown:
        dominant = (
            row.dominant_failure_kind.value if row.dominant_failure_kind is not None else "none"
        )
        lines.append(
            f"| {row.workflow_type} | {row.checked} | {row.passed} | {row.failed} | "
            f"{row.skipped} | {row.errored} | {dominant} | {row.risk_level.value} | "
            f"{row.notes or ''} |"
        )

    lines.extend(["", "### Top failing histories"])
    if view.top_failures:
        for index, result in enumerate(view.top_failures, start=1):
            lines.extend(
                [
                    f"{index}. `{result.path}` — `{result.workflow_type}`  ",
                    f"   **Kind:** {result.failure_kind}  ",
                    f"   **Summary:** {result.summary}  ",
                    f"   **Likely cause:** {result.likely_cause or '-'}  ",
                    f"   **Hint:** {result.remediation_hint or '-'}",
                    "",
                ]
            )
    else:
        lines.append("- none")

    lines.extend(["### Artifacts"])
    if view.artifacts:
        for artifact in view.artifacts:
            lines.append(f"- {artifact.label}: `{artifact.path}`")
    else:
        lines.append("- none")

    return "\n".join(lines).rstrip() + "\n"


def render_github_summary(report: VerificationReport) -> str:
    return render_markdown_report(report)


def write_markdown_report(report: VerificationReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown_report(report), encoding="utf-8")
    return output_path
