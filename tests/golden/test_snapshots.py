from __future__ import annotations

from pathlib import Path

from replaygate.reporting.console import render_console_summary
from replaygate.reporting.json_report import render_json_report
from replaygate.reporting.markdown_report import render_markdown_report
from tests.support import sample_report

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def test_json_snapshot() -> None:
    rendered = render_json_report(sample_report())
    expected = (SNAPSHOT_DIR / "report.json").read_text(encoding="utf-8")
    assert rendered == expected


def test_markdown_snapshot() -> None:
    rendered = render_markdown_report(sample_report())
    expected = (SNAPSHOT_DIR / "report.md").read_text(encoding="utf-8")
    assert rendered == expected


def test_console_snapshot() -> None:
    rendered = render_console_summary(sample_report())
    expected = (SNAPSHOT_DIR / "console.txt").read_text(encoding="utf-8")
    assert rendered == expected
