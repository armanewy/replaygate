"""JSON report rendering."""

from __future__ import annotations

import json
from pathlib import Path

from replaygate.models import VerificationReport


def render_json_report(report: VerificationReport) -> str:
    payload = report.model_dump(mode="json", exclude_none=True)
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_json_report(report: VerificationReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_json_report(report), encoding="utf-8")
    return output_path
