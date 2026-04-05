from __future__ import annotations

from replaygate.reporting.console import render_console_summary
from replaygate.reporting.json_report import render_json_report
from replaygate.reporting.markdown_report import render_markdown_report
from tests.support import sample_report


def test_render_json_report_is_stable() -> None:
    rendered = render_json_report(sample_report())

    assert '"project_name": "payments-workflows"' in rendered
    assert '"kind": "nondeterminism"' in rendered


def test_render_markdown_report_contains_failure_details() -> None:
    rendered = render_markdown_report(sample_report())

    assert "# Replay Gate Report" in rendered
    assert "command mismatch during replay" in rendered
    assert "max_failures=0 -> violated (1 observed)" in rendered


def test_render_console_summary_contains_expected_sections() -> None:
    rendered = render_console_summary(sample_report())

    assert "Replay Gate: FAILED" in rendered
    assert "Top failures:" in rendered
    assert "kind: nondeterminism" in rendered
