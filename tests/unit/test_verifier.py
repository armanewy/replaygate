from __future__ import annotations

import asyncio
from pathlib import Path

from replaygate.adapters.base import WorkflowAdapter
from replaygate.config import ReplayGateConfig
from replaygate.models import (
    CompatibilityStatus,
    ReplayCandidate,
    ReplayResult,
    ReplayStatus,
    RiskLevel,
    WorkflowEngine,
    WorkflowHistoryArtifact,
    WorkflowIdentifier,
)
from replaygate.verifier import verify_config


class FakeAdapter(WorkflowAdapter):
    engine = WorkflowEngine.TEMPORAL

    def load_candidate(self, config: ReplayGateConfig, config_path: Path) -> ReplayCandidate:
        return ReplayCandidate(
            engine=self.engine,
            source="fake.module",
            registered_workflow_types=["PaymentWorkflow"],
        )

    def discover_histories(
        self,
        config: ReplayGateConfig,
        config_path: Path,
    ) -> list[WorkflowHistoryArtifact]:
        return [
            WorkflowHistoryArtifact(
                engine=self.engine,
                path="histories/payment.json",
                source_kind="filesystem",
                checksum_sha256="abc",
                size_bytes=10,
                workflow=WorkflowIdentifier(
                    workflow_id="payment-1",
                    workflow_type="PaymentWorkflow",
                    run_id="run-1",
                ),
            )
        ]

    async def replay_artifact(
        self,
        artifact: WorkflowHistoryArtifact,
        candidate: ReplayCandidate,
        config: ReplayGateConfig,
        config_path: Path,
    ) -> ReplayResult:
        return ReplayResult(
            artifact=artifact,
            workflow_type="PaymentWorkflow",
            status=ReplayStatus.PASSED,
            compatibility_status=CompatibilityStatus.COMPATIBLE,
            risk_level=RiskLevel.LOW,
        )


def test_verify_config_writes_outputs(tmp_path: Path) -> None:
    config_path = tmp_path / "replaygate.yaml"
    config_path.write_text(
        """project:
  name: demo
  engine: temporal
verification:
  workflow_types:
    - PaymentWorkflow
  history_sources:
    - type: filesystem
      path: ./histories
      glob: "*.json"
  selection:
    max_histories: 10
    strategy: all
  outputs:
    json: ./artifacts/report.json
    markdown: ./artifacts/report.md
    html: ./artifacts/report.html
policy:
  fail_on: []
  max_unknown: 0
  max_failures: 0
privacy:
  redact_payloads_in_reports: true
temporal:
  import_mode: local_module
  workflows_module: fake.module
  payload_codec: none
""",
        encoding="utf-8",
    )

    execution = asyncio.run(verify_config(config_path, adapter=FakeAdapter()))

    assert execution.exit_code == 0
    assert execution.report.summary.passed == 1
    assert execution.report.summary.workflow_types == 1
    assert execution.report.artifacts.json_report == "artifacts/report.json"
    assert (tmp_path / "artifacts" / "report.json").exists()
    assert (tmp_path / "artifacts" / "report.md").exists()
    assert (tmp_path / "artifacts" / "report.html").exists()


def test_verify_config_builds_missing_history_result(tmp_path: Path) -> None:
    class EmptyAdapter(FakeAdapter):
        def discover_histories(
            self,
            config: ReplayGateConfig,
            config_path: Path,
        ) -> list[WorkflowHistoryArtifact]:
            return []

    config_path = tmp_path / "replaygate.yaml"
    config_path.write_text(
        """project:
  name: demo
  engine: temporal
verification:
  history_sources:
    - type: filesystem
      path: ./histories
      glob: "*.json"
  selection:
    max_histories: 10
    strategy: all
policy:
  fail_on:
    - missing_history
  max_unknown: 0
  max_failures: 0
temporal:
  import_mode: local_module
  workflows_module: fake.module
  payload_codec: none
""",
        encoding="utf-8",
    )

    execution = asyncio.run(verify_config(config_path, adapter=EmptyAdapter()))

    assert execution.exit_code == 1
    assert execution.report.results[0].failure is not None
    assert execution.report.results[0].failure.kind.value == "missing_history"
