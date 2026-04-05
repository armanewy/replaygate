from __future__ import annotations

import json
from pathlib import Path

from replaygate.adapters.temporal.loader import discover_histories
from replaygate.config import load_config


def test_discover_histories_keeps_distinct_records_for_duplicate_basenames(
    tmp_path: Path,
) -> None:
    project_dir = tmp_path / "project"
    source_a = tmp_path / "external-a"
    source_b = tmp_path / "external-b"
    project_dir.mkdir()
    source_a.mkdir()
    source_b.mkdir()

    payload_template = {
        "run_id": "run-1",
        "workflow_type": "PaymentWorkflow",
        "history": {"events": []},
    }
    (source_a / "history.json").write_text(
        json.dumps({"workflow_id": "payment-a", **payload_template}),
        encoding="utf-8",
    )
    (source_b / "history.json").write_text(
        json.dumps({"workflow_id": "payment-b", **payload_template}),
        encoding="utf-8",
    )

    config_path = project_dir / "replaygate.yaml"
    config_path.write_text(
        f"""project:
  name: demo
  engine: temporal
verification:
  history_sources:
    - type: filesystem
      path: {source_a.as_posix()}
      glob: "*.json"
    - type: filesystem
      path: {source_b.as_posix()}
      glob: "*.json"
  selection:
    max_histories: 10
    strategy: all
policy:
  fail_on: []
  max_unknown: 0
  max_failures: 0
temporal:
  import_mode: local_module
  workflows_module: examples.temporal.workflows
  payload_codec: none
""",
        encoding="utf-8",
    )

    config = load_config(config_path)
    artifacts, records = discover_histories(config, config_path)

    assert len(artifacts) == 2
    assert len(records) == 2
    assert len({artifact.path for artifact in artifacts}) == 2
    assert len({artifact.metadata["record_key"] for artifact in artifacts}) == 2
