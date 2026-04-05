from __future__ import annotations

from replaygate.reporting.console import render_console_summary
from replaygate.reporting.html_report import render_html_report
from replaygate.reporting.json_report import render_json_report
from replaygate.reporting.markdown_report import render_markdown_report
from tests.support import sample_report


def test_render_json_report_is_stable() -> None:
    rendered = render_json_report(sample_report())

    assert '"project": {' in rendered
    assert '"tool_version": "0.1.0"' in rendered
    assert '"kind": "nondeterminism"' in rendered


def test_render_markdown_report_contains_failure_details() -> None:
    rendered = render_markdown_report(sample_report())

    assert "## Replay Gate — FAILED" in rendered
    assert "command mismatch during replay" in rendered
    assert "max_failures=0 -> violated (1 observed)" in rendered


def test_render_console_summary_contains_expected_sections() -> None:
    rendered = render_console_summary(sample_report())

    assert "Replay Gate 0.1.0" in rendered
    assert "VERDICT: FAILED" in rendered
    assert "Top failing histories:" in rendered
    assert "kind: nondeterminism" in rendered


def test_render_html_report_contains_expected_sections() -> None:
    rendered = render_html_report(sample_report())

    assert "<title>Replay Gate Report - payments-workflows</title>" in rendered
    assert "Top Failing Histories" in rendered
    assert "Environment And Config Snapshot" in rendered
