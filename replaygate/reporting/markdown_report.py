"""Markdown report rendering."""

from __future__ import annotations

from pathlib import Path

from replaygate.models import ReplayStatus, VerificationReport


def render_markdown_report(report: VerificationReport) -> str:
    status = "PASSED" if report.policy.passed else "FAILED"
    lines = [
        "# Replay Gate Report",
        "",
        f"- Status: **{status}**",
        f"- Project: `{report.project_name}`",
        f"- Engine: `{report.engine.value}`",
        f"- Histories checked: `{report.summary.total_histories}`",
        f"- Passed: `{report.summary.passed}`",
        f"- Failed: `{report.summary.failed}`",
        f"- Errors: `{report.summary.errors}`",
        f"- Skipped: `{report.summary.skipped}`",
        "",
        "## Policy",
        "",
    ]

    if report.policy.violated_rules:
        for rule in report.policy.violated_rules:
            lines.append(f"- {rule}")
    else:
        lines.append("- all checks passed")

    lines.extend(["", "## Results", ""])
    for result in report.results:
        lines.append(f"### {result.workflow_type or 'unknown-workflow'} / `{result.artifact.path}`")
        lines.append("")
        lines.append(f"- Status: `{result.status.value}`")
        lines.append(f"- Compatibility: `{result.compatibility_status.value}`")
        lines.append(f"- Risk: `{result.risk_level.value}`")
        if result.failure is not None:
            lines.append(f"- Failure kind: `{result.failure.kind.value}`")
            lines.append(f"- Summary: {result.failure.summary}")
            lines.append(f"- Likely cause: {result.failure.likely_cause}")
            lines.append(f"- Remediation: {result.failure.remediation_hint}")
        lines.append("")

    failures = [
        result
        for result in report.results
        if result.status in {ReplayStatus.FAILED, ReplayStatus.ERROR} and result.failure is not None
    ]
    if failures:
        lines.extend(["## Top Failures", ""])
        for index, result in enumerate(failures[:5], start=1):
            failure = result.failure
            assert failure is not None
            workflow_name = result.workflow_type or "unknown-workflow"
            lines.append(f"{index}. `{workflow_name}` / `{result.artifact.path}`")
            lines.append(f"   - kind: `{failure.kind.value}`")
            lines.append(f"   - summary: {failure.summary}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_markdown_report(report: VerificationReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown_report(report), encoding="utf-8")
    return output_path
