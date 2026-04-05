from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from replaygate.cli import app
from replaygate.models import FailureKind, VerificationReport

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples" / "temporal"
HISTORIES_DIR = EXAMPLES_DIR / "histories"


def write_config(
    tmp_path: Path,
    *,
    workflow_module: str,
    history_globs: list[str],
    fail_on: list[str],
) -> Path:
    source_lines = []
    for glob_name in history_globs:
        source_lines.extend(
            [
                "    - type: filesystem",
                f'      path: "{HISTORIES_DIR.as_posix()}"',
                f'      glob: "{glob_name}"',
            ]
        )
    fail_on_lines = [f"    - {name}" for name in fail_on]
    config_path = tmp_path / "replaygate.yaml"
    config_path.write_text(
        "\n".join(
            [
                "project:",
                "  name: integration-demo",
                "  engine: temporal",
                "",
                "verification:",
                "  history_sources:",
                *source_lines,
                "  selection:",
                "    max_histories: 50",
                "    strategy: all",
                "  outputs:",
                "    json: ./artifacts/report.json",
                "    markdown: ./artifacts/report.md",
                "    html: ./artifacts/report.html",
                "",
                "policy:",
                "  fail_on:",
                *fail_on_lines,
                "  max_unknown: 0",
                "  max_failures: 0",
                "",
                "privacy:",
                "  redact_payloads_in_reports: true",
                "",
                "temporal:",
                "  import_mode: local_module",
                f"  workflows_module: {workflow_module}",
                "  payload_codec: none",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config_path


def test_temporal_cli_passes_with_compatible_workflows(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        workflow_module="examples.temporal.workflows",
        history_globs=["payment_history.json", "refund_history.json"],
        fail_on=["nondeterminism", "unknown_workflow_type", "adapter_error"],
    )
    runner = CliRunner()

    result = runner.invoke(app, ["verify", "--config", str(config_path)])

    assert result.exit_code == 0
    assert "VERDICT: PASSED" in result.stdout
    report = VerificationReport.model_validate_json(
        (tmp_path / "artifacts" / "report.json").read_text(encoding="utf-8")
    )
    assert report.summary.passed == 2
    assert (tmp_path / "artifacts" / "report.html").exists()


def test_temporal_cli_fails_with_nondeterminism(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        workflow_module="examples.temporal.workflows_breaking",
        history_globs=["payment_history.json", "refund_history.json"],
        fail_on=["nondeterminism", "unknown_workflow_type", "adapter_error"],
    )
    runner = CliRunner()

    result = runner.invoke(app, ["verify", "--config", str(config_path)])

    assert result.exit_code == 1
    assert "kind: nondeterminism" in result.stdout
    report = VerificationReport.model_validate_json(
        (tmp_path / "artifacts" / "report.json").read_text(encoding="utf-8")
    )
    failure_kinds = {replay.failure.kind for replay in report.results if replay.failure is not None}
    assert FailureKind.NONDETERMINISM in failure_kinds


def test_temporal_cli_reports_unknown_workflow_type(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        workflow_module="examples.temporal.workflows",
        history_globs=["legacy_history.json"],
        fail_on=["unknown_workflow_type"],
    )
    runner = CliRunner()

    result = runner.invoke(app, ["verify", "--config", str(config_path)])

    assert result.exit_code == 1
    report = VerificationReport.model_validate_json(
        (tmp_path / "artifacts" / "report.json").read_text(encoding="utf-8")
    )
    assert report.results[0].failure is not None
    assert report.results[0].failure.kind is FailureKind.UNKNOWN_WORKFLOW_TYPE


def test_temporal_cli_reports_corrupted_history(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        workflow_module="examples.temporal.workflows",
        history_globs=["corrupted_history.json"],
        fail_on=["corrupted_history"],
    )
    runner = CliRunner()

    result = runner.invoke(app, ["verify", "--config", str(config_path)])

    assert result.exit_code == 1
    report = VerificationReport.model_validate_json(
        (tmp_path / "artifacts" / "report.json").read_text(encoding="utf-8")
    )
    assert report.results[0].failure is not None
    assert report.results[0].failure.kind is FailureKind.CORRUPTED_HISTORY


def test_temporal_cli_json_mode_emits_machine_report(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        workflow_module="examples.temporal.workflows",
        history_globs=["payment_history.json"],
        fail_on=["nondeterminism"],
    )
    runner = CliRunner()

    result = runner.invoke(app, ["verify", "--config", str(config_path), "--json"])

    assert result.exit_code == 0
    assert '"tool_version": "0.1.0"' in result.stdout


def test_report_command_rerenders_html(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        workflow_module="examples.temporal.workflows_breaking",
        history_globs=["payment_history.json"],
        fail_on=["nondeterminism"],
    )
    runner = CliRunner()
    verify_result = runner.invoke(app, ["verify", "--config", str(config_path)])

    assert verify_result.exit_code == 1
    output_path = tmp_path / "rerendered.html"
    report_result = runner.invoke(
        app,
        [
            "report",
            "--input",
            str(tmp_path / "artifacts" / "report.json"),
            "--html",
            str(output_path),
        ],
    )

    assert report_result.exit_code == 0
    assert output_path.exists()
    assert "<title>Replay Gate Report - integration-demo</title>" in output_path.read_text(
        encoding="utf-8"
    )
