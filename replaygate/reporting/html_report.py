"""Static HTML report rendering."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from pathlib import Path

from jinja2 import Environment, Template, select_autoescape

from replaygate.models import VerificationReport, WorkflowTypeBreakdown
from replaygate.reporting.view_models import build_report_view
from replaygate.risk import risk_rank


def _workflow_sort_key(row: WorkflowTypeBreakdown) -> tuple[int, int, int, str]:
    return (
        -risk_rank(row.risk_level),
        -row.failed,
        -row.errored,
        row.workflow_type,
    )


@lru_cache
def _load_resource(resource_path: str) -> str:
    return files("replaygate.reporting").joinpath(resource_path).read_text(encoding="utf-8")


@lru_cache
def _compiled_template() -> Template:
    environment = Environment(
        autoescape=select_autoescape(enabled_extensions=("html",)),
    )
    return environment.from_string(_load_resource("templates/report.html.j2"))


def render_html_report(report: VerificationReport) -> str:
    view = build_report_view(report, top_failures_limit=8)
    template = _compiled_template()
    failure_max = max((item.count for item in view.failure_breakdown), default=0)
    workflow_rows = tuple(sorted(view.workflow_breakdown, key=_workflow_sort_key))
    workflow_filters = sorted({item.workflow_type for item in view.results})
    failure_filters = sorted(
        {item.failure_kind for item in view.results if item.failure_kind is not None}
    )
    dominant_failure = view.failure_breakdown[0] if view.failure_breakdown else None
    top_failure = view.top_failures[0] if view.top_failures else None
    highlight_workflow = next(
        (row for row in workflow_rows if row.failed or row.errored),
        workflow_rows[0] if workflow_rows else None,
    )
    top_likely_cause = (
        top_failure.likely_cause
        if top_failure and top_failure.likely_cause
        else (
            "No likely cause classified."
            if view.failed
            else "No replay failures classified."
        )
    )
    top_remediation = (
        top_failure.remediation_hint
        if top_failure and top_failure.remediation_hint
        else (
            "No remediation hint classified."
            if view.failed
            else "No remediation required."
        )
    )
    diagnosis_heading = "Why this failed" if view.policy_decision == "fail" else "Why this passed"
    section_links = (
        {"id": "why-this-failed", "label": diagnosis_heading},
        {"id": "verification-summary", "label": "Verification Summary"},
        {"id": "workflow-type-breakdown", "label": "Affected Workflow Types"},
        {"id": "top-failing-histories", "label": "Top Failing Histories"},
        {"id": "all-results", "label": "All Results"},
        {"id": "advanced-details", "label": "Advanced Details"},
    )
    return template.render(
        view=view,
        diagnosis_heading=diagnosis_heading,
        dominant_failure=dominant_failure,
        failure_filters=failure_filters,
        failure_max=failure_max,
        highlight_workflow=highlight_workflow,
        section_links=section_links,
        stylesheet=_load_resource("static/report.css"),
        script=_load_resource("static/report.js"),
        top_likely_cause=top_likely_cause,
        top_remediation=top_remediation,
        workflow_filters=workflow_filters,
        workflow_rows=workflow_rows,
    )


def write_html_report(report: VerificationReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_html_report(report), encoding="utf-8")
    return output_path
